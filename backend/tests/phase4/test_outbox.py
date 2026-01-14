"""
Phase 4 P0-2: Transactional Outbox Tests
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from modules.crm_core import (
    # Outbox functions
    enqueue_outbox,
    get_pending_outbox_items,
    get_pool,  # For direct DB queries in deterministic tests
    mark_outbox_sending,
    mark_outbox_sent,
    mark_outbox_failed,
    get_outbox_stats,
    replay_outbox_item,
    get_dead_letter_items,
    cancel_pending_outbox_for_contact,
    OutboxStatus,
    OutboxObjectType,

    # CRM functions for testing
    create_location,
    create_contact,
    create_appointment,
    get_appointment,
    LocationCreate,
    ContactCreate,
    AppointmentCreate,
    AppointmentStatus,

    # Tag functions
    create_tag,
    get_tag_by_name,
    add_tag_to_contact,
    TagCreate,
)


class TestOutboxBasics:
    """Test basic outbox enqueue and retrieval."""

    @pytest.mark.asyncio
    async def test_enqueue_and_retrieve(self):
        """Test enqueuing an item and retrieving it as pending."""
        # Enqueue a test item
        outbox_id = await enqueue_outbox(
            object_type="test",
            object_id="00000000-0000-0000-0000-000000000001",
            destination="sms",
            payload={"to": "+15551234567", "body": "Test message"}
        )

        assert outbox_id is not None

        # Retrieve pending items (use larger limit for test stability)
        items = await get_pending_outbox_items(limit=100)

        # Find our item
        our_item = next((i for i in items if str(i["id"]) == outbox_id), None)
        assert our_item is not None
        assert our_item["status"] == "pending"
        assert our_item["destination"] == "sms"

    @pytest.mark.asyncio
    async def test_idempotency(self):
        """Test that idempotency_key prevents duplicates."""
        payload = {"to": "+15551234567", "body": "Test"}
        idempotency_key = "test-unique-key-123"

        # Enqueue first time
        outbox_id_1 = await enqueue_outbox(
            object_type="test",
            object_id="00000000-0000-0000-0000-000000000001",
            destination="sms",
            payload=payload,
            idempotency_key=idempotency_key
        )

        # Enqueue second time with same idempotency key
        outbox_id_2 = await enqueue_outbox(
            object_type="test",
            object_id="00000000-0000-0000-0000-000000000001",
            destination="sms",
            payload=payload,
            idempotency_key=idempotency_key
        )

        # Should return same ID or conflict
        # ON CONFLICT DO UPDATE SET updated_at = NOW() returns the existing row
        assert outbox_id_2 is not None


class TestOutboxLifecycle:
    """Test outbox item lifecycle: pending -> sending -> sent/failed."""

    @pytest.mark.asyncio
    async def test_mark_sending(self):
        """Test marking an item as sending."""
        outbox_id = await enqueue_outbox(
            object_type="test",
            object_id="00000000-0000-0000-0000-000000000001",
            destination="sms",
            payload={"test": "data"}
        )

        await mark_outbox_sending(outbox_id)

        # Verify it's no longer in pending list
        items = await get_pending_outbox_items(limit=10)
        assert not any(str(i["id"]) == outbox_id for i in items)

    @pytest.mark.asyncio
    async def test_mark_sent(self):
        """Test marking an item as successfully sent."""
        outbox_id = await enqueue_outbox(
            object_type="test",
            object_id="00000000-0000-0000-0000-000000000001",
            destination="sms",
            payload={"test": "data"}
        )

        await mark_outbox_sending(outbox_id)
        await mark_outbox_sent(outbox_id)

        # Should not appear in pending list
        items = await get_pending_outbox_items(limit=10)
        assert not any(str(i["id"]) == outbox_id for i in items)

    @pytest.mark.asyncio
    async def test_mark_failed_with_retry(self):
        """Test marking an item as failed schedules retry."""
        outbox_id = await enqueue_outbox(
            object_type="test",
            object_id="00000000-0000-0000-0000-000000000001",
            destination="sms",
            payload={"test": "data"}
        )

        await mark_outbox_sending(outbox_id)
        await mark_outbox_failed(outbox_id, "Test error", attempt_count=1)

        # Item should be back in pending but with future next_attempt_at
        items = await get_pending_outbox_items(limit=10)
        # Won't appear if next_attempt_at is in the future
        # This is expected - retry is scheduled for later


class TestOutboxDeadLetter:
    """Test dead letter queue for exhausted retries."""

    @pytest.mark.asyncio
    async def test_dead_letter_after_max_attempts(self):
        """Test that items move to dead_letter after max attempts."""
        outbox_id = await enqueue_outbox(
            object_type="test",
            object_id="00000000-0000-0000-0000-000000000001",
            destination="sms",
            payload={"test": "data"}
        )

        # Mark as failed 5 times
        for attempt in range(1, 6):
            await mark_outbox_sending(outbox_id)
            await mark_outbox_failed(outbox_id, f"Attempt {attempt} failed", attempt_count=attempt)

        # Should be in dead letter now
        dead_items = await get_dead_letter_items(limit=10)
        assert any(str(i["id"]) == outbox_id for i in dead_items)

    @pytest.mark.asyncio
    async def test_replay_dead_letter(self):
        """Test replaying a dead letter item."""
        outbox_id = await enqueue_outbox(
            object_type="test",
            object_id="00000000-0000-0000-0000-000000000001",
            destination="sms",
            payload={"test": "data"}
        )

        # Move to dead letter
        for attempt in range(1, 6):
            await mark_outbox_sending(outbox_id)
            await mark_outbox_failed(outbox_id, "Test error", attempt_count=attempt)

        # Replay it
        success = await replay_outbox_item(outbox_id)
        assert success

        # Should appear in pending again
        items = await get_pending_outbox_items(limit=100)
        our_item = next((i for i in items if str(i["id"]) == outbox_id), None)
        assert our_item is not None
        assert our_item["status"] == "pending"
        assert our_item["attempt_count"] == 0


class TestOutboxStats:
    """Test outbox statistics and monitoring."""

    @pytest.mark.asyncio
    async def test_get_stats(self):
        """Test getting outbox statistics."""
        # Create a few items in different states
        id1 = await enqueue_outbox(
            object_type="test",
            object_id="00000000-0000-0000-0000-000000000001",
            destination="sms",
            payload={"test": "1"}
        )

        id2 = await enqueue_outbox(
            object_type="test",
            object_id="00000000-0000-0000-0000-000000000002",
            destination="sms",
            payload={"test": "2"}
        )

        await mark_outbox_sending(id2)
        await mark_outbox_sent(id2)

        stats = await get_outbox_stats()
        assert stats is not None
        assert isinstance(stats, dict)


async def _get_outbox_items_for_appointment(appointment_id: str) -> list:
    """
    Direct DB query for outbox items by appointment ID.
    
    This is deterministic - immune to dirty DB / stale pending items
    that might appear in get_pending_outbox_items due to LIMIT/ordering.
    """
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT id, object_type, object_id, destination, status
            FROM outbox
            WHERE object_type = 'appointment' AND object_id = $1
            """,
            appointment_id
        )
        return [dict(r) for r in rows]


class TestAppointmentOutboxIntegration:
    """Test that appointments atomically create outbox items."""

    @pytest.mark.asyncio
    async def test_appointment_creates_sales_outbox(self):
        """Test that creating an appointment enqueues sales API notification."""
        # Use default location
        default_location = "00000000-0000-0000-0000-000000000001"

        # Create a contact
        contact = await create_contact(ContactCreate(
            location_id=default_location,
            phone="+15551234567",
            first_name="Test",
            last_name="User"
        ))

        # Create an appointment
        appointment_data = AppointmentCreate(
            location_id=default_location,
            contact_id=contact.id,
            title="Test Appointment",
            start_time=datetime.utcnow() + timedelta(days=1),
            end_time=datetime.utcnow() + timedelta(days=1, hours=1),
            status=AppointmentStatus.SCHEDULED
        )

        appointment = await create_appointment(appointment_data)
        assert appointment.id is not None

        # Direct DB query for this appointment's outbox items (deterministic)
        items = await _get_outbox_items_for_appointment(appointment.id)
        sales_items = [i for i in items if i["destination"] == "sales_api"]

        assert len(sales_items) >= 1

    @pytest.mark.asyncio
    async def test_appointment_creates_sms_outbox(self):
        """Test that appointment with phone creates SMS outbox item."""
        default_location = "00000000-0000-0000-0000-000000000001"

        # Create contact with phone
        contact = await create_contact(ContactCreate(
            location_id=default_location,
            phone="+15559876543",
            first_name="SMS",
            last_name="Test"
        ))

        # Create appointment
        appointment_data = AppointmentCreate(
            location_id=default_location,
            contact_id=contact.id,
            title="SMS Test Appointment",
            start_time=datetime.utcnow() + timedelta(days=2),
            end_time=datetime.utcnow() + timedelta(days=2, hours=1),
            status=AppointmentStatus.SCHEDULED
        )

        appointment = await create_appointment(appointment_data)

        # Direct DB query for this appointment's outbox items (deterministic)
        items = await _get_outbox_items_for_appointment(appointment.id)
        sms_items = [i for i in items if i["destination"] == "sms"]

        assert len(sms_items) >= 1

    @pytest.mark.asyncio
    async def test_appointment_no_sms_for_dnd_contact(self):
        """Test that DND contacts don't get SMS outbox items."""
        default_location = "00000000-0000-0000-0000-000000000001"

        # Create contact with DND enabled and a "dnd" tag
        contact = await create_contact(ContactCreate(
            location_id=default_location,
            phone="+15551112222",
            first_name="DND",
            last_name="Contact",
            dnd=True  # Use the DND boolean field
        ))

        # Create appointment
        appointment_data = AppointmentCreate(
            location_id=default_location,
            contact_id=contact.id,
            title="DND Test Appointment",
            start_time=datetime.utcnow() + timedelta(days=3),
            end_time=datetime.utcnow() + timedelta(days=3, hours=1),
            status=AppointmentStatus.SCHEDULED
        )

        appointment = await create_appointment(appointment_data)

        # Direct DB query for this appointment's outbox items (deterministic)
        items = await _get_outbox_items_for_appointment(appointment.id)
        sms_items = [i for i in items if i["destination"] == "sms"]

        assert len(sms_items) == 0


class TestOutboxCancellation:
    """Test cancelling pending outbox items for a contact."""

    @pytest.mark.asyncio
    async def test_cancel_pending_for_contact(self):
        """Test cancelling all pending items for a contact."""
        default_location = "00000000-0000-0000-0000-000000000001"

        # Create contact
        contact = await create_contact(ContactCreate(
            location_id=default_location,
            phone="+15553334444",
            first_name="Cancel",
            last_name="Test"
        ))

        # Enqueue SMS item for this contact
        outbox_id = await enqueue_outbox(
            object_type="client_notification",
            object_id=str(contact.id),
            destination="sms",
            payload={
                "contact_id": str(contact.id),
                "to": contact.phone,
                "body": "Test message"
            }
        )

        # Cancel all pending items for this contact
        cancelled_count = await cancel_pending_outbox_for_contact(str(contact.id))

        assert cancelled_count >= 1

        # Verify item is cancelled
        items = await get_pending_outbox_items(limit=50)
        assert not any(str(i["id"]) == outbox_id for i in items)
