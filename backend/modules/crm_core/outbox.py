"""
Transactional Outbox for Guaranteed Delivery

Ensures critical notifications (appointments, confirmations) are never lost.
Uses atomic database transactions + background worker for reliable delivery.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from enum import Enum
import json

from .executor import get_pool

logger = logging.getLogger(__name__)


class OutboxStatus(str, Enum):
    PENDING = "pending"
    SENDING = "sending"
    SENT = "sent"
    FAILED = "failed"
    DEAD_LETTER = "dead_letter"
    CANCELLED = "cancelled"


class OutboxObjectType(str, Enum):
    APPOINTMENT = "appointment"
    CLIENT_NOTIFICATION = "client_notification"
    SALES_NOTIFICATION = "sales_notification"
    EMAIL = "email"


# Retry backoff schedule (in seconds)
RETRY_BACKOFF = [60, 300, 900, 1800, 3600]  # 1m, 5m, 15m, 30m, 1h


async def enqueue_outbox(
    object_type: str,
    object_id: str,
    destination: str,
    payload: Dict[str, Any],
    destination_config: Optional[Dict[str, Any]] = None,
    idempotency_key: Optional[str] = None,
    conn=None
) -> str:
    """
    Add an item to the outbox for guaranteed delivery.

    This should be called within the same transaction as the main operation
    (e.g., appointment creation) to ensure atomicity.

    Args:
        object_type: Type of object (appointment, notification, etc.)
        object_id: UUID of the object
        destination: Where to deliver (sales_api, email, sms, slack)
        payload: The data to deliver
        destination_config: Optional config (URL, email, etc.)
        idempotency_key: Optional key for deduplication
        conn: Optional database connection (for transactional usage)

    Returns:
        outbox_id: UUID of the created outbox entry
    """
    if conn:
        # Use provided connection (part of transaction)
        result = await conn.fetchrow(
            """
            INSERT INTO outbox (
                object_type, object_id, destination, destination_config,
                payload, idempotency_key
            ) VALUES ($1, $2, $3, $4, $5, $6)
            ON CONFLICT (idempotency_key) WHERE idempotency_key IS NOT NULL
            DO UPDATE SET updated_at = NOW()
            RETURNING id
            """,
            object_type,
            object_id,
            destination,
            json.dumps(destination_config or {}),
            json.dumps(payload),
            idempotency_key
        )
        outbox_id = str(result["id"])
        logger.info(f"Outbox entry created: {outbox_id} for {object_type}/{object_id}")
        return outbox_id
    else:
        # Get new connection from pool
        pool = await get_pool()
        async with pool.acquire() as conn:
            result = await conn.fetchrow(
                """
                INSERT INTO outbox (
                    object_type, object_id, destination, destination_config,
                    payload, idempotency_key
                ) VALUES ($1, $2, $3, $4, $5, $6)
                ON CONFLICT (idempotency_key) WHERE idempotency_key IS NOT NULL
                DO UPDATE SET updated_at = NOW()
                RETURNING id
                """,
                object_type,
                object_id,
                destination,
                json.dumps(destination_config or {}),
                json.dumps(payload),
                idempotency_key
            )

            outbox_id = str(result["id"])
            logger.info(f"Outbox entry created: {outbox_id} for {object_type}/{object_id}")
            return outbox_id


async def get_pending_outbox_items(limit: int = 50) -> List[Dict]:
    """
    Fetch pending outbox items ready for processing.
    Uses SELECT FOR UPDATE SKIP LOCKED for safe concurrent processing.
    """
    pool = await get_pool()
    async with pool.acquire() as conn:
        results = await conn.fetch(
            """
            SELECT * FROM outbox
            WHERE status IN ('pending', 'failed')
            AND next_attempt_at <= NOW()
            AND attempt_count < max_attempts
            ORDER BY next_attempt_at ASC
            LIMIT $1
            FOR UPDATE SKIP LOCKED
            """,
            limit
        )
        return [dict(r) for r in results]


async def mark_outbox_sending(outbox_id: str) -> None:
    """Mark an outbox item as currently being processed."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """
            UPDATE outbox
            SET status = 'sending', attempt_count = attempt_count + 1, updated_at = NOW()
            WHERE id = $1
            """,
            outbox_id
        )


async def mark_outbox_sent(outbox_id: str) -> None:
    """Mark an outbox item as successfully delivered."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """
            UPDATE outbox
            SET status = 'sent', sent_at = NOW(), updated_at = NOW()
            WHERE id = $1
            """,
            outbox_id
        )
        logger.info(f"Outbox item {outbox_id} delivered successfully")


async def mark_outbox_failed(outbox_id: str, error: str, attempt_count: int) -> None:
    """
    Mark an outbox item as failed, schedule retry or dead letter.
    """
    # Calculate next retry time
    backoff_index = min(attempt_count, len(RETRY_BACKOFF) - 1)
    backoff_seconds = RETRY_BACKOFF[backoff_index]
    next_attempt = datetime.utcnow() + timedelta(seconds=backoff_seconds)

    # Check if we've exhausted retries
    if attempt_count >= 5:
        status = "dead_letter"
        logger.error(f"Outbox item {outbox_id} moved to dead letter after {attempt_count} attempts: {error}")
    else:
        status = "failed"
        logger.warning(f"Outbox item {outbox_id} failed (attempt {attempt_count}), retry at {next_attempt}: {error}")

    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """
            UPDATE outbox
            SET status = $2, last_error = $3, last_error_at = NOW(),
                next_attempt_at = $4, updated_at = NOW()
            WHERE id = $1
            """,
            outbox_id, status, error, next_attempt
        )


async def get_outbox_stats() -> Dict[str, Any]:
    """Get outbox statistics for monitoring dashboard."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        results = await conn.fetch(
            """
            SELECT
                status,
                COUNT(*) as count,
                MIN(created_at) as oldest,
                MAX(attempt_count) as max_attempts
            FROM outbox
            GROUP BY status
            """
        )

        stats = {row["status"]: {"count": row["count"], "oldest": row["oldest"]} for row in results}

        # Add pending age alert
        pending_result = await conn.fetchrow(
            """
            SELECT EXTRACT(EPOCH FROM (NOW() - MIN(created_at))) as oldest_pending_seconds
            FROM outbox WHERE status = 'pending'
            """
        )
        stats["oldest_pending_seconds"] = pending_result["oldest_pending_seconds"] if pending_result and pending_result["oldest_pending_seconds"] else 0

        return stats


async def replay_outbox_item(outbox_id: str) -> bool:
    """
    Manually replay a failed/dead_letter outbox item.
    Used by admin to retry after fixing underlying issue.
    """
    pool = await get_pool()
    async with pool.acquire() as conn:
        result = await conn.fetchrow(
            """
            UPDATE outbox
            SET status = 'pending', attempt_count = 0, next_attempt_at = NOW(), updated_at = NOW()
            WHERE id = $1
            RETURNING id
            """,
            outbox_id
        )
        if result:
            logger.info(f"Outbox item {outbox_id} replayed by admin")
            return True
        return False


async def get_dead_letter_items(limit: int = 100) -> List[Dict]:
    """Get dead letter items for admin review."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        results = await conn.fetch(
            """
            SELECT * FROM outbox
            WHERE status = 'dead_letter'
            ORDER BY updated_at DESC
            LIMIT $1
            """,
            limit
        )
        return [dict(r) for r in results]


async def cancel_pending_outbox_for_contact(contact_id: str) -> int:
    """
    Cancel all pending outbox items for a contact (e.g., when they opt out).

    Args:
        contact_id: Contact UUID

    Returns:
        Number of items cancelled
    """
    pool = await get_pool()
    async with pool.acquire() as conn:
        # Cancel pending SMS notifications for this contact
        result = await conn.execute(
            """
            UPDATE outbox
            SET status = 'cancelled', updated_at = NOW()
            WHERE status IN ('pending', 'failed')
            AND destination = 'sms'
            AND payload->>'contact_id' = $1
            """,
            contact_id
        )

        # Extract count from result string like "UPDATE 5"
        count = int(result.split()[-1]) if result and result.startswith('UPDATE') else 0
        if count > 0:
            logger.info(f"Cancelled {count} pending outbox items for contact {contact_id}")
        return count
