"""
Ziloss CRM Core - Database Operations
"""

import os
import json
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
import asyncpg

from .models import (
    Contact, ContactCreate, ContactUpdate, ContactFilter,
    Tag, TagCreate,
    Conversation, ConversationCreate, ConversationFilter, ConversationWithContact,
    Message, MessageCreate,
    Appointment, AppointmentCreate, AppointmentUpdate, AppointmentFilter,
    Location, LocationCreate
)

logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv(
    'DATABASE_URL', 
    'postgresql://postgres:postgres@localhost:5433/orchestrator'
)

# Connection pool
_pool: Optional[asyncpg.Pool] = None


async def get_pool() -> asyncpg.Pool:
    """Get or create connection pool."""
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(DATABASE_URL, min_size=2, max_size=10)
    return _pool


async def close_pool():
    """Close connection pool."""
    global _pool
    if _pool:
        await _pool.close()
        _pool = None


# ============================================
# LOCATION OPERATIONS
# ============================================

async def create_location(data: LocationCreate) -> Location:
    """Create a new location."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            INSERT INTO locations (
                name, slug, timezone, phone, email, address1, city, state,
                postal_code, country, settings, business_hours
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
            RETURNING *
        """,
            data.name, data.slug, data.timezone, data.phone, data.email,
            data.address1, data.city, data.state, data.postal_code, data.country,
            json.dumps(data.settings), json.dumps(data.business_hours)
        )
        return _row_to_location(row)


async def get_location(location_id: str) -> Optional[Location]:
    """Get location by ID."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM locations WHERE id = $1", location_id
        )
        return _row_to_location(row) if row else None


async def list_locations() -> List[Location]:
    """List all locations."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT * FROM locations ORDER BY name")
        return [_row_to_location(row) for row in rows]


def _row_to_location(row) -> Location:
    # Handle JSONB fields - they might be dicts or strings depending on driver
    settings = row['settings'] if row['settings'] else {}
    if isinstance(settings, str):
        settings = json.loads(settings) if settings else {}

    business_hours = row.get('business_hours', {})
    if isinstance(business_hours, str):
        business_hours = json.loads(business_hours) if business_hours else {}

    return Location(
        id=str(row['id']),
        name=row['name'],
        slug=row['slug'],
        timezone=row['timezone'],
        phone=row.get('phone'),
        email=row.get('email'),
        address1=row.get('address1'),
        city=row.get('city'),
        state=row.get('state'),
        postal_code=row.get('postal_code'),
        country=row.get('country', 'US'),
        settings=settings,
        business_hours=business_hours,
        created_at=row['created_at'],
        updated_at=row['updated_at']
    )


# ============================================
# TAG OPERATIONS
# ============================================

async def create_tag(data: TagCreate) -> Tag:
    """Create a new tag."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            INSERT INTO tags (location_id, name, color)
            VALUES ($1, $2, $3)
            ON CONFLICT (location_id, name) DO UPDATE SET color = $3
            RETURNING *
        """, data.location_id, data.name, data.color)
        return _row_to_tag(row)


async def get_tag(tag_id: str) -> Optional[Tag]:
    """Get tag by ID."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM tags WHERE id = $1", tag_id)
        return _row_to_tag(row) if row else None


async def get_tag_by_name(location_id: str, name: str) -> Optional[Tag]:
    """Get tag by name in location."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM tags WHERE location_id = $1 AND name = $2",
            location_id, name
        )
        return _row_to_tag(row) if row else None


async def list_tags(location_id: str) -> List[Tag]:
    """List all tags for a location."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT * FROM tags WHERE location_id = $1 ORDER BY name",
            location_id
        )
        return [_row_to_tag(row) for row in rows]


def _row_to_tag(row) -> Tag:
    return Tag(
        id=str(row['id']),
        location_id=str(row['location_id']),
        name=row['name'],
        color=row['color'],
        created_at=row['created_at']
    )


# ============================================
# CONTACT OPERATIONS
# ============================================

async def create_contact(data: ContactCreate) -> Contact:
    """Create a new contact."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            INSERT INTO contacts (
                location_id, first_name, last_name, email, phone,
                address1, address2, city, state, postal_code, country,
                company_name, website, source, medium, assigned_to, type,
                dnd, dnd_settings, custom_fields
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20)
            RETURNING *
        """,
            data.location_id, data.first_name, data.last_name, data.email, data.phone,
            data.address1, data.address2, data.city, data.state, data.postal_code, data.country,
            data.company_name, data.website, data.source, data.medium, data.assigned_to, data.type.value,
            data.dnd, json.dumps(data.dnd_settings), json.dumps(data.custom_fields)
        )
        return await _row_to_contact(conn, row)


async def get_contact(contact_id: str) -> Optional[Contact]:
    """Get contact by ID with tags."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM contacts WHERE id = $1", contact_id
        )
        return await _row_to_contact(conn, row) if row else None


async def update_contact(contact_id: str, data: ContactUpdate) -> Optional[Contact]:
    """Update a contact."""
    pool = await get_pool()
    
    # Build dynamic update query
    updates = []
    values = []
    idx = 1
    
    for field, value in data.model_dump(exclude_unset=True).items():
        if value is not None:
            if field in ('dnd_settings', 'custom_fields'):
                value = json.dumps(value)
            elif field == 'type':
                value = value.value
            updates.append(f"{field} = ${idx}")
            values.append(value)
            idx += 1
    
    if not updates:
        return await get_contact(contact_id)
    
    values.append(contact_id)
    query = f"""
        UPDATE contacts SET {', '.join(updates)}
        WHERE id = ${idx}
        RETURNING *
    """
    
    async with pool.acquire() as conn:
        row = await conn.fetchrow(query, *values)
        return await _row_to_contact(conn, row) if row else None


async def delete_contact(contact_id: str) -> bool:
    """Delete a contact."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        result = await conn.execute(
            "DELETE FROM contacts WHERE id = $1", contact_id
        )
        return result == "DELETE 1"


async def list_contacts(filter: ContactFilter) -> List[Contact]:
    """List contacts with filtering."""
    pool = await get_pool()
    
    query = "SELECT * FROM contacts WHERE location_id = $1"
    values = [filter.location_id]
    idx = 2
    
    if filter.search:
        query += f""" AND (
            first_name ILIKE ${idx} OR 
            last_name ILIKE ${idx} OR 
            email ILIKE ${idx} OR 
            phone ILIKE ${idx}
        )"""
        values.append(f"%{filter.search}%")
        idx += 1
    
    if filter.type:
        query += f" AND type = ${idx}"
        values.append(filter.type.value)
        idx += 1
    
    if filter.dnd is not None:
        query += f" AND dnd = ${idx}"
        values.append(filter.dnd)
        idx += 1
    
    if filter.source:
        query += f" AND source = ${idx}"
        values.append(filter.source)
        idx += 1
    
    if filter.tag:
        query += f""" AND id IN (
            SELECT contact_id FROM contact_tags ct
            JOIN tags t ON ct.tag_id = t.id
            WHERE t.name = ${idx}
        )"""
        values.append(filter.tag)
        idx += 1
    
    query += f" ORDER BY created_at DESC LIMIT ${idx} OFFSET ${idx + 1}"
    values.extend([filter.limit, filter.offset])
    
    async with pool.acquire() as conn:
        rows = await conn.fetch(query, *values)
        return [await _row_to_contact(conn, row) for row in rows]


async def add_tag_to_contact(contact_id: str, tag_name: str, added_by: str = "system") -> bool:
    """Add a tag to a contact. Creates tag if doesn't exist."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        # Get contact's location
        contact = await conn.fetchrow(
            "SELECT location_id FROM contacts WHERE id = $1", contact_id
        )
        if not contact:
            return False
        
        location_id = str(contact['location_id'])
        
        # Create or get tag
        tag_row = await conn.fetchrow("""
            INSERT INTO tags (location_id, name)
            VALUES ($1, $2)
            ON CONFLICT (location_id, name) DO UPDATE SET name = $2
            RETURNING id
        """, location_id, tag_name)
        
        # Add to contact
        await conn.execute("""
            INSERT INTO contact_tags (contact_id, tag_id, added_by)
            VALUES ($1, $2, $3)
            ON CONFLICT (contact_id, tag_id) DO NOTHING
        """, contact_id, tag_row['id'], added_by)
        
        return True


async def remove_tag_from_contact(contact_id: str, tag_name: str) -> bool:
    """Remove a tag from a contact."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        result = await conn.execute("""
            DELETE FROM contact_tags
            WHERE contact_id = $1 AND tag_id IN (
                SELECT t.id FROM tags t
                JOIN contacts c ON t.location_id = c.location_id
                WHERE c.id = $1 AND t.name = $2
            )
        """, contact_id, tag_name)
        return "DELETE 1" in result


async def get_contact_tags(conn, contact_id: str) -> List[str]:
    """Get tag names for a contact."""
    rows = await conn.fetch("""
        SELECT t.name FROM tags t
        JOIN contact_tags ct ON t.id = ct.tag_id
        WHERE ct.contact_id = $1
        ORDER BY t.name
    """, contact_id)
    return [row['name'] for row in rows]


async def find_contact_by_phone(phone: str, location_id: Optional[str] = None) -> Optional[Contact]:
    """
    Find contact by phone number with normalization.

    Args:
        phone: Phone number to search for
        location_id: Optional location ID to scope search

    Returns:
        Contact if found, None otherwise
    """
    pool = await get_pool()

    # Normalize phone number - strip all non-digits
    normalized = ''.join(filter(str.isdigit, phone))

    # If 10 digits, prepend country code
    if len(normalized) == 10:
        normalized = '1' + normalized

    # Search by last 10 digits to handle variations (+1, 1, etc)
    search_pattern = f"%{normalized[-10:]}"

    async with pool.acquire() as conn:
        if location_id:
            query = """
                SELECT * FROM contacts
                WHERE REGEXP_REPLACE(phone, '[^0-9]', '', 'g') LIKE $1
                AND location_id = $2
                LIMIT 1
            """
            row = await conn.fetchrow(query, search_pattern, location_id)
        else:
            query = """
                SELECT * FROM contacts
                WHERE REGEXP_REPLACE(phone, '[^0-9]', '', 'g') LIKE $1
                LIMIT 1
            """
            row = await conn.fetchrow(query, search_pattern)

        return await _row_to_contact(conn, row) if row else None


async def _row_to_contact(conn, row) -> Contact:
    tags = await get_contact_tags(conn, str(row['id']))

    # Handle JSONB fields
    dnd_settings = row['dnd_settings'] if row['dnd_settings'] else {}
    if isinstance(dnd_settings, str):
        dnd_settings = json.loads(dnd_settings) if dnd_settings else {}

    custom_fields = row['custom_fields'] if row['custom_fields'] else {}
    if isinstance(custom_fields, str):
        custom_fields = json.loads(custom_fields) if custom_fields else {}

    return Contact(
        id=str(row['id']),
        location_id=str(row['location_id']),
        first_name=row['first_name'],
        last_name=row['last_name'],
        email=row['email'],
        phone=row['phone'],
        address1=row['address1'],
        address2=row['address2'],
        city=row['city'],
        state=row['state'],
        postal_code=row['postal_code'],
        country=row['country'],
        company_name=row.get('company_name'),
        website=row.get('website'),
        source=row['source'],
        medium=row.get('medium'),
        assigned_to=str(row['assigned_to']) if row['assigned_to'] else None,
        type=row['type'],
        dnd=row['dnd'],
        dnd_settings=dnd_settings,
        custom_fields=custom_fields,
        created_at=row['created_at'],
        updated_at=row['updated_at'],
        last_contacted_at=row['last_contacted_at'],
        tags=tags
    )


# ============================================
# CONVERSATION OPERATIONS
# ============================================

async def create_conversation(data: ConversationCreate) -> Conversation:
    """Create a new conversation."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            INSERT INTO conversations (
                location_id, contact_id, channel, channel_id, status, assigned_to
            )
            VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING *
        """,
            data.location_id, data.contact_id, data.channel.value,
            data.channel_id, data.status.value, data.assigned_to
        )
        return _row_to_conversation(row)


async def get_conversation(conversation_id: str) -> Optional[Conversation]:
    """Get conversation by ID."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM conversations WHERE id = $1", conversation_id
        )
        return _row_to_conversation(row) if row else None


async def get_or_create_conversation(
    location_id: str, 
    contact_id: str, 
    channel: str = "sms"
) -> Conversation:
    """Get existing conversation or create new one."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        # Try to find existing
        row = await conn.fetchrow("""
            SELECT * FROM conversations 
            WHERE contact_id = $1 AND channel = $2
            ORDER BY updated_at DESC
            LIMIT 1
        """, contact_id, channel)
        
        if row:
            return _row_to_conversation(row)
        
        # Create new
        row = await conn.fetchrow("""
            INSERT INTO conversations (location_id, contact_id, channel)
            VALUES ($1, $2, $3)
            RETURNING *
        """, location_id, contact_id, channel)
        return _row_to_conversation(row)


async def list_conversations(filter: ConversationFilter) -> List[Conversation]:
    """List conversations with filtering."""
    pool = await get_pool()
    
    query = "SELECT * FROM conversations WHERE location_id = $1"
    values = [filter.location_id]
    idx = 2
    
    if filter.contact_id:
        query += f" AND contact_id = ${idx}"
        values.append(filter.contact_id)
        idx += 1
    
    if filter.status:
        query += f" AND status = ${idx}"
        values.append(filter.status.value)
        idx += 1
    
    if filter.channel:
        query += f" AND channel = ${idx}"
        values.append(filter.channel.value)
        idx += 1
    
    query += f" ORDER BY last_message_at DESC NULLS LAST, updated_at DESC LIMIT ${idx} OFFSET ${idx + 1}"
    values.extend([filter.limit, filter.offset])
    
    async with pool.acquire() as conn:
        rows = await conn.fetch(query, *values)
        return [_row_to_conversation(row) for row in rows]


async def update_conversation_last_message(
    conversation_id: str, 
    body: str, 
    direction: str
):
    """Update conversation's last message cache."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            UPDATE conversations
            SET last_message_body = $2,
                last_message_direction = $3,
                last_message_at = NOW(),
                unread_count = CASE WHEN $3::text = 'inbound' THEN unread_count + 1 ELSE unread_count END
            WHERE id = $1
        """, conversation_id, body[:500] if body else None, direction)


async def update_conversation_status(conversation_id: str, status: str) -> bool:
    """
    Update conversation status.

    Args:
        conversation_id: UUID of conversation
        status: New status ('open', 'closed', 'needs_human', etc.)

    Returns:
        True if updated, False if not found
    """
    pool = await get_pool()
    async with pool.acquire() as conn:
        result = await conn.execute("""
            UPDATE conversations
            SET status = $2, updated_at = NOW()
            WHERE id = $1
        """, conversation_id, status)

        # Parse affected row count from result string "UPDATE N"
        affected = int(result.split()[-1]) if result else 0

        if affected > 0:
            logger.info(f"Conversation {conversation_id} status updated to '{status}'")
            return True
        else:
            logger.warning(f"Conversation {conversation_id} not found for status update")
            return False


def _row_to_conversation(row) -> Conversation:
    return Conversation(
        id=str(row['id']),
        location_id=str(row['location_id']),
        contact_id=str(row['contact_id']),
        channel=row['channel'],
        channel_id=row['channel_id'],
        status=row['status'],
        unread_count=row['unread_count'],
        assigned_to=str(row['assigned_to']) if row['assigned_to'] else None,
        last_message_body=row['last_message_body'],
        last_message_direction=row['last_message_direction'],
        last_message_at=row['last_message_at'],
        created_at=row['created_at'],
        updated_at=row['updated_at']
    )


# ============================================
# MESSAGE OPERATIONS
# ============================================

async def create_message(data: MessageCreate) -> Message:
    """Create a new message."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            INSERT INTO messages (
                conversation_id, contact_id, direction, body, media_urls, channel,
                external_id, status, ai_generated, ai_model, sentiment, intent
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
            RETURNING *
        """,
            data.conversation_id, data.contact_id, data.direction.value, data.body,
            data.media_urls, data.channel.value, data.external_id,
            data.status.value, data.ai_generated, data.ai_model,
            data.sentiment, data.intent
        )
        
        # Update conversation cache
        await update_conversation_last_message(
            data.conversation_id, 
            data.body, 
            data.direction.value
        )
        
        # Update contact last_contacted_at if outbound
        if data.direction.value == "outbound":
            await conn.execute("""
                UPDATE contacts SET last_contacted_at = NOW()
                WHERE id = (SELECT contact_id FROM conversations WHERE id = $1)
            """, data.conversation_id)
        
        return _row_to_message(row)


async def get_message(message_id: str) -> Optional[Message]:
    """Get message by ID."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM messages WHERE id = $1", message_id
        )
        return _row_to_message(row) if row else None


async def list_messages(conversation_id: str, limit: int = 100, offset: int = 0) -> List[Message]:
    """List messages in a conversation."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT * FROM messages
            WHERE conversation_id = $1
            ORDER BY created_at DESC
            LIMIT $2 OFFSET $3
        """, conversation_id, limit, offset)
        return [_row_to_message(row) for row in rows]


async def update_message_status(
    external_id: str,
    status: str,
    error_message: Optional[str] = None
) -> bool:
    """
    Update message status by Twilio SID (external_id).

    Args:
        external_id: Twilio message SID
        status: New status (queued, sent, delivered, failed, etc.)
        error_message: Optional error message if failed

    Returns:
        True if message was updated, False if not found
    """
    pool = await get_pool()
    async with pool.acquire() as conn:
        # Update message status
        result = await conn.execute("""
            UPDATE messages
            SET status = $2, error_message = $3, updated_at = NOW()
            WHERE external_id = $1
        """, external_id, status, error_message)

        # Check if any row was updated
        return "UPDATE 1" in result


def _row_to_message(row) -> Message:
    return Message(
        id=str(row['id']),
        conversation_id=str(row['conversation_id']),
        contact_id=str(row['contact_id']),
        direction=row['direction'],
        body=row['body'],
        media_urls=row['media_urls'] or [],
        channel=row['channel'],
        external_id=row['external_id'],
        status=row['status'],
        error_message=row.get('error_message'),
        ai_generated=row['ai_generated'],
        ai_model=row['ai_model'],
        sentiment=row['sentiment'],
        intent=row['intent'],
        created_at=row['created_at'],
        updated_at=row['updated_at'],
        delivered_at=row.get('delivered_at'),
        read_at=row.get('read_at')
    )


# ============================================
# APPOINTMENT OPERATIONS
# ============================================

async def create_appointment(data: AppointmentCreate) -> Appointment:
    """
    Create a new appointment with guaranteed delivery notifications.

    Uses transactional outbox pattern to ensure appointment creation and
    notification delivery are atomic. Enqueues:
    1. Sales API notification (always)
    2. Client SMS confirmation (if phone exists and not DND)
    """
    # Import here to avoid circular dependency
    from .outbox import enqueue_outbox

    pool = await get_pool()
    async with pool.acquire() as conn:
        # Begin transaction
        async with conn.transaction():
            # Create appointment
            row = await conn.fetchrow("""
                INSERT INTO appointments (
                    location_id, contact_id, title, description, start_time, end_time,
                    timezone, status, location, assigned_to, notes, calendar_id, external_id
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
                RETURNING *
            """,
                data.location_id, data.contact_id, data.title, data.description,
                data.start_time, data.end_time, data.timezone,
                data.status.value, data.location, data.assigned_to,
                data.notes, data.calendar_id, data.external_id
            )
            appointment = _row_to_appointment(row)

            # Enqueue sales API notification (always)
            sales_payload = {
                "appointment_id": str(appointment.id),
                "location_id": str(appointment.location_id),
                "contact_id": str(appointment.contact_id),
                "title": appointment.title,
                "start_time": appointment.start_time.isoformat(),
                "end_time": appointment.end_time.isoformat(),
                "status": appointment.status.value,
            }

            await enqueue_outbox(
                object_type="appointment",
                object_id=str(appointment.id),
                destination="sales_api",
                payload=sales_payload,
                idempotency_key=f"appt-sales-{appointment.id}",
                conn=conn
            )

            # Get contact to check phone and DND status
            contact = await _row_to_contact(conn, await conn.fetchrow(
                "SELECT * FROM contacts WHERE id = $1",
                appointment.contact_id
            ))

            if contact and contact.phone:
                # Check DND status - must check both dnd field and dnd_settings
                is_dnd = contact.dnd if contact.dnd is not None else False

                # Check dnd_settings.sms if dnd_settings exists
                if not is_dnd and hasattr(contact, 'dnd_settings') and contact.dnd_settings:
                    if isinstance(contact.dnd_settings, dict) and contact.dnd_settings.get("sms"):
                        is_dnd = True

                if not is_dnd:
                    # Enqueue client SMS confirmation
                    sms_body = (
                        f"Appointment confirmed: {appointment.title}\n"
                        f"Time: {appointment.start_time.strftime('%b %d at %I:%M %p')}\n"
                        f"Location: {appointment.location or 'TBD'}"
                    )

                    sms_payload = {
                        "appointment_id": str(appointment.id),
                        "to": contact.phone,
                        "body": sms_body,
                        "location_id": str(appointment.location_id),
                        "contact_id": str(contact.id),
                    }

                    await enqueue_outbox(
                        object_type="appointment",
                        object_id=str(appointment.id),
                        destination="sms",
                        payload=sms_payload,
                        idempotency_key=f"appt-confirm-{appointment.id}",
                        conn=conn
                    )

            return appointment


async def get_appointment(appointment_id: str) -> Optional[Appointment]:
    """Get appointment by ID."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM appointments WHERE id = $1", appointment_id
        )
        return _row_to_appointment(row) if row else None


async def update_appointment(appointment_id: str, data: AppointmentUpdate) -> Optional[Appointment]:
    """Update an appointment."""
    pool = await get_pool()
    
    updates = []
    values = []
    idx = 1
    
    for field, value in data.model_dump(exclude_unset=True).items():
        if value is not None:
            if field == 'status':
                value = value.value
            updates.append(f"{field} = ${idx}")
            values.append(value)
            idx += 1
    
    if not updates:
        return await get_appointment(appointment_id)
    
    values.append(appointment_id)
    query = f"""
        UPDATE appointments SET {', '.join(updates)}
        WHERE id = ${idx}
        RETURNING *
    """
    
    async with pool.acquire() as conn:
        row = await conn.fetchrow(query, *values)
        return _row_to_appointment(row) if row else None


async def list_appointments(filter: AppointmentFilter) -> List[Appointment]:
    """List appointments with filtering."""
    pool = await get_pool()
    
    query = "SELECT * FROM appointments WHERE location_id = $1"
    values = [filter.location_id]
    idx = 2
    
    if filter.contact_id:
        query += f" AND contact_id = ${idx}"
        values.append(filter.contact_id)
        idx += 1
    
    if filter.status:
        query += f" AND status = ${idx}"
        values.append(filter.status.value)
        idx += 1
    
    if filter.start_after:
        query += f" AND start_time >= ${idx}"
        values.append(filter.start_after)
        idx += 1
    
    if filter.start_before:
        query += f" AND start_time <= ${idx}"
        values.append(filter.start_before)
        idx += 1
    
    query += f" ORDER BY start_time ASC LIMIT ${idx} OFFSET ${idx + 1}"
    values.extend([filter.limit, filter.offset])
    
    async with pool.acquire() as conn:
        rows = await conn.fetch(query, *values)
        return [_row_to_appointment(row) for row in rows]


def _row_to_appointment(row) -> Appointment:
    return Appointment(
        id=str(row['id']),
        location_id=str(row['location_id']),
        contact_id=str(row['contact_id']),
        title=row['title'],
        description=row.get('description'),
        start_time=row['start_time'],
        end_time=row['end_time'],
        timezone=row['timezone'],
        status=row['status'],
        location=row.get('location'),
        assigned_to=str(row['assigned_to']) if row.get('assigned_to') else None,
        notes=row.get('notes'),
        calendar_id=row.get('calendar_id'),
        external_id=row.get('external_id'),
        reminder_sent=row['reminder_sent'],
        reminder_sent_at=row.get('reminder_sent_at'),
        created_at=row['created_at'],
        updated_at=row['updated_at']
    )


async def get_conversation_messages(
    conversation_id: str,
    limit: int = 50
) -> List[Dict[str, Any]]:
    """
    Get recent messages for a conversation.

    Args:
        conversation_id: Conversation UUID
        limit: Maximum number of messages to return

    Returns:
        List of message dictionaries with basic fields
    """
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT
                id, contact_id, conversation_id, body,
                direction, status, created_at
            FROM messages
            WHERE conversation_id = $1
            ORDER BY created_at DESC
            LIMIT $2
            """,
            conversation_id, limit
        )

        # Return as simple dicts for AI context
        messages = []
        for row in reversed(rows):  # Reverse to get chronological order
            messages.append({
                'id': str(row['id']),
                'contact_id': str(row['contact_id']) if row['contact_id'] else None,
                'conversation_id': str(row['conversation_id']),
                'body': row['body'],
                'direction': row['direction'],
                'status': row['status'],
                'created_at': row['created_at'].isoformat() if row['created_at'] else None
            })

        return messages


async def update_message(
    message_id: str,
    ai_intent: Optional[str] = None,
    ai_sentiment: Optional[str] = None,
    ai_confidence: Optional[float] = None
) -> bool:
    """
    Update message with AI analysis results.

    Args:
        message_id: Message UUID
        ai_intent: Detected intent from AI (saved to 'intent' column)
        ai_sentiment: Detected sentiment from AI (saved to 'sentiment' column)
        ai_confidence: Confidence score (0.0 to 1.0) - NOTE: not stored, for future use

    Returns:
        True if updated successfully
    """
    pool = await get_pool()
    async with pool.acquire() as conn:
        update_fields = []
        params = [message_id]
        param_count = 2

        # Map ai_intent to 'intent' column
        if ai_intent is not None:
            update_fields.append(f"intent = ${param_count}")
            params.append(ai_intent)
            param_count += 1

        # Map ai_sentiment to 'sentiment' column
        if ai_sentiment is not None:
            update_fields.append(f"sentiment = ${param_count}")
            params.append(ai_sentiment)
            param_count += 1

        # ai_confidence not stored in current schema - log for debugging
        if ai_confidence is not None:
            logger.debug(f"AI confidence for message {message_id}: {ai_confidence}")

        if not update_fields:
            return False

        update_fields.append("updated_at = NOW()")

        query = f"""
            UPDATE messages
            SET {', '.join(update_fields)}
            WHERE id = $1
        """

        await conn.execute(query, *params)
        return True


# ============================================
# TWILIO PHONE NUMBER MAPPING
# ============================================

def normalize_phone_e164(phone: str) -> str:
    """
    Normalize phone number to E.164 format (+15551234567).

    Handles:
    - (555) 123-4567 -> +15551234567
    - 555.123.4567 -> +15551234567
    - +1 555 123 4567 -> +15551234567
    - 15551234567 -> +15551234567
    - 5551234567 -> +15551234567
    """
    import re

    # Remove all non-digits
    digits = re.sub(r'\D', '', phone)

    # Handle US numbers
    if len(digits) == 10:
        return f"+1{digits}"
    elif len(digits) == 11 and digits.startswith('1'):
        return f"+{digits}"
    elif len(digits) > 11:
        # Assume international with country code
        return f"+{digits}"
    else:
        # Return as-is with + prefix
        return f"+{digits}"


async def get_location_id_from_twilio_number(phone_number: str) -> Optional[str]:
    """
    Map a Twilio 'To' number to its owning location_id.

    Args:
        phone_number: The Twilio number that received the SMS (any format)

    Returns:
        location_id (UUID string) or None if not found
    """
    # Normalize to E.164
    normalized = normalize_phone_e164(phone_number)

    pool = await get_pool()
    async with pool.acquire() as conn:
        result = await conn.fetchrow(
            """
            SELECT location_id
            FROM twilio_phone_numbers
            WHERE phone_number = $1 AND is_active = TRUE
            LIMIT 1
            """,
            normalized
        )

        if result:
            return str(result["location_id"])

        return None


async def register_twilio_number(
    phone_number: str,
    location_id: str,
    twilio_sid: Optional[str] = None,
    friendly_name: Optional[str] = None
) -> dict:
    """
    Register a Twilio phone number for a location.

    Args:
        phone_number: Twilio number in any format
        location_id: UUID of the owning location
        twilio_sid: Optional Twilio Phone Number SID
        friendly_name: Optional human readable name

    Returns:
        Created record as dict
    """
    normalized = normalize_phone_e164(phone_number)

    pool = await get_pool()
    async with pool.acquire() as conn:
        result = await conn.fetchrow(
            """
            INSERT INTO twilio_phone_numbers (phone_number, location_id, twilio_sid, friendly_name)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (phone_number) WHERE is_active = TRUE
            DO UPDATE SET
                location_id = EXCLUDED.location_id,
                twilio_sid = COALESCE(EXCLUDED.twilio_sid, twilio_phone_numbers.twilio_sid),
                friendly_name = COALESCE(EXCLUDED.friendly_name, twilio_phone_numbers.friendly_name),
                updated_at = NOW()
            RETURNING *
            """,
            normalized, location_id, twilio_sid, friendly_name
        )

        return dict(result)


async def list_twilio_numbers_for_location(location_id: str) -> List[dict]:
    """Get all Twilio numbers registered to a location."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        results = await conn.fetch(
            """
            SELECT * FROM twilio_phone_numbers
            WHERE location_id = $1 AND is_active = TRUE
            ORDER BY created_at
            """,
            location_id
        )
        return [dict(r) for r in results]


# ============================================
# MODULE EXECUTOR INTERFACE
# ============================================

async def execute(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Execute CRM action (module interface)."""
    action = inputs.get('action')
    
    try:
        if action == 'create_contact':
            data = ContactCreate(**inputs['data'])
            result = await create_contact(data)
            return {'success': True, 'contact': result.model_dump()}
        
        elif action == 'get_contact':
            result = await get_contact(inputs['contact_id'])
            return {'success': True, 'contact': result.model_dump() if result else None}
        
        elif action == 'list_contacts':
            filter = ContactFilter(**inputs.get('filter', {}))
            results = await list_contacts(filter)
            return {'success': True, 'contacts': [c.model_dump() for c in results]}
        
        elif action == 'add_tag':
            result = await add_tag_to_contact(
                inputs['contact_id'], 
                inputs['tag_name'],
                inputs.get('added_by', 'system')
            )
            return {'success': result}
        
        elif action == 'remove_tag':
            result = await remove_tag_from_contact(
                inputs['contact_id'], 
                inputs['tag_name']
            )
            return {'success': result}
        
        elif action == 'create_message':
            data = MessageCreate(**inputs['data'])
            result = await create_message(data)
            return {'success': True, 'message': result.model_dump()}
        
        elif action == 'create_appointment':
            data = AppointmentCreate(**inputs['data'])
            result = await create_appointment(data)
            return {'success': True, 'appointment': result.model_dump()}
        
        else:
            return {'success': False, 'error': f'Unknown action: {action}'}
    
    except Exception as e:
        logger.exception(f"CRM action failed: {action}")
        return {'success': False, 'error': str(e)}
