"""
Ziloss CRM API Routes

FastAPI router for CRM operations.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from datetime import datetime

from modules.crm_core import (
    # Models
    Contact, ContactCreate, ContactUpdate, ContactFilter,
    Tag, TagCreate,
    Conversation, ConversationCreate, ConversationFilter,
    Message, MessageCreate,
    Appointment, AppointmentCreate, AppointmentUpdate, AppointmentFilter,
    Location, LocationCreate,
    ContactType, ConversationStatus, AppointmentStatus, Channel,

    # Operations
    create_location, get_location, list_locations,
    create_contact, get_contact, update_contact, delete_contact, list_contacts,
    add_tag_to_contact, remove_tag_from_contact,
    create_tag, list_tags,
    create_conversation, get_conversation, list_conversations, get_or_create_conversation,
    create_message, list_messages,
    create_appointment, get_appointment, update_appointment, list_appointments,

    # Twilio Phone Number Mapping
    get_location_id_from_twilio_number, register_twilio_number, list_twilio_numbers_for_location,

    # Outbox
    get_outbox_stats, get_dead_letter_items, replay_outbox_item,
)

router = APIRouter(prefix="/crm", tags=["CRM"])


# ============================================
# LOCATION ENDPOINTS
# ============================================

@router.post("/locations", response_model=Location, status_code=201)
async def api_create_location(data: LocationCreate):
    """Create a new location (workspace/tenant)."""
    return await create_location(data)


@router.get("/locations", response_model=List[Location])
async def api_list_locations():
    """List all locations."""
    return await list_locations()


@router.get("/locations/{location_id}", response_model=Location)
async def api_get_location(location_id: str):
    """Get a location by ID."""
    location = await get_location(location_id)
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    return location


# ============================================
# CONTACT ENDPOINTS
# ============================================

@router.post("/contacts", response_model=Contact, status_code=201)
async def api_create_contact(data: ContactCreate):
    """Create a new contact."""
    return await create_contact(data)


@router.get("/contacts", response_model=List[Contact])
async def api_list_contacts(
    location_id: str = Query(..., description="Location ID"),
    search: Optional[str] = Query(None, description="Search in name, email, phone"),
    tag: Optional[str] = Query(None, description="Filter by tag name"),
    type: Optional[ContactType] = Query(None, description="Filter by type"),
    dnd: Optional[bool] = Query(None, description="Filter by DND status"),
    source: Optional[str] = Query(None, description="Filter by source"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0)
):
    """List contacts with optional filtering."""
    filter = ContactFilter(
        location_id=location_id,
        search=search,
        tag=tag,
        type=type,
        dnd=dnd,
        source=source,
        limit=limit,
        offset=offset
    )
    return await list_contacts(filter)


@router.get("/contacts/{contact_id}", response_model=Contact)
async def api_get_contact(contact_id: str):
    """Get a contact by ID."""
    contact = await get_contact(contact_id)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    return contact


@router.patch("/contacts/{contact_id}", response_model=Contact)
async def api_update_contact(contact_id: str, data: ContactUpdate):
    """Update a contact."""
    contact = await update_contact(contact_id, data)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    return contact


@router.delete("/contacts/{contact_id}", status_code=204)
async def api_delete_contact(contact_id: str):
    """Delete a contact."""
    deleted = await delete_contact(contact_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Contact not found")


@router.post("/contacts/{contact_id}/tags/{tag_name}", status_code=201)
async def api_add_tag_to_contact(
    contact_id: str, 
    tag_name: str,
    added_by: str = Query("api", description="Who added the tag")
):
    """Add a tag to a contact. Creates tag if it doesn't exist."""
    success = await add_tag_to_contact(contact_id, tag_name, added_by)
    if not success:
        raise HTTPException(status_code=404, detail="Contact not found")
    return {"status": "ok", "tag": tag_name}


@router.delete("/contacts/{contact_id}/tags/{tag_name}", status_code=204)
async def api_remove_tag_from_contact(contact_id: str, tag_name: str):
    """Remove a tag from a contact."""
    await remove_tag_from_contact(contact_id, tag_name)


# ============================================
# TAG ENDPOINTS
# ============================================

@router.post("/tags", response_model=Tag, status_code=201)
async def api_create_tag(data: TagCreate):
    """Create a new tag."""
    return await create_tag(data)


@router.get("/tags", response_model=List[Tag])
async def api_list_tags(location_id: str = Query(..., description="Location ID")):
    """List all tags for a location."""
    return await list_tags(location_id)


# ============================================
# CONVERSATION ENDPOINTS
# ============================================

@router.post("/conversations", response_model=Conversation, status_code=201)
async def api_create_conversation(data: ConversationCreate):
    """Create a new conversation."""
    return await create_conversation(data)


@router.get("/conversations", response_model=List[Conversation])
async def api_list_conversations(
    location_id: str = Query(..., description="Location ID"),
    contact_id: Optional[str] = Query(None, description="Filter by contact"),
    status: Optional[ConversationStatus] = Query(None, description="Filter by status"),
    channel: Optional[Channel] = Query(None, description="Filter by channel"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0)
):
    """List conversations with optional filtering."""
    filter = ConversationFilter(
        location_id=location_id,
        contact_id=contact_id,
        status=status,
        channel=channel,
        limit=limit,
        offset=offset
    )
    return await list_conversations(filter)


@router.get("/conversations/{conversation_id}", response_model=Conversation)
async def api_get_conversation(conversation_id: str):
    """Get a conversation by ID."""
    conv = await get_conversation(conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conv


@router.get("/conversations/{conversation_id}/messages", response_model=List[Message])
async def api_list_conversation_messages(
    conversation_id: str,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0)
):
    """List messages in a conversation."""
    return await list_messages(conversation_id, limit, offset)


# ============================================
# MESSAGE ENDPOINTS
# ============================================

@router.post("/messages", response_model=Message, status_code=201)
async def api_create_message(data: MessageCreate):
    """Create a new message."""
    return await create_message(data)


@router.post("/messages/send-sms")
async def api_send_sms(sms_request: dict):
    """
    Send SMS to a contact via Twilio.

    Flow:
    1. Validate contact exists
    2. Get phone number
    3. Find or create conversation
    4. Send via Twilio
    5. Create message record with external_id
    6. Return message_id and twilio_sid
    """
    from modules.twilio_sms import TwilioSMSExecutor, SendSMSRequest

    # Parse request
    request = SendSMSRequest(**sms_request)

    # Get contact if contact_id provided
    contact = None
    to_number = request.to

    if request.contact_id:
        contact = await get_contact(request.contact_id)
        if not contact:
            raise HTTPException(status_code=404, detail="Contact not found")
        to_number = contact.phone
        if not to_number:
            raise HTTPException(status_code=400, detail="Contact has no phone number")

    # Find or create conversation
    conversation_id = request.conversation_id

    if not conversation_id and request.contact_id:
        conversation = await get_or_create_conversation(
            location_id=request.location_id,
            contact_id=request.contact_id,
            channel="sms"
        )
        conversation_id = conversation.id

    # Send via Twilio
    twilio = TwilioSMSExecutor()
    twilio_request = SendSMSRequest(
        to=to_number,
        body=request.body,
        location_id=request.location_id,
        contact_id=request.contact_id,
        conversation_id=conversation_id
    )

    result = await twilio.send_sms(twilio_request)

    if not result.success:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to send SMS: {result.error}"
        )

    # Create message record
    if conversation_id:
        message_data = MessageCreate(
            conversation_id=conversation_id,
            contact_id=request.contact_id or "",
            channel="sms",
            direction="outbound",
            body=request.body,
            status="queued",
            external_id=result.message_sid
        )
        message = await create_message(message_data)

        return {
            "success": True,
            "message_id": message.id,
            "twilio_sid": result.message_sid,
            "status": "queued"
        }
    else:
        # No conversation (sent to arbitrary number without contact)
        return {
            "success": True,
            "message_id": None,
            "twilio_sid": result.message_sid,
            "status": "queued"
        }


# ============================================
# APPOINTMENT ENDPOINTS
# ============================================

@router.post("/appointments", response_model=Appointment, status_code=201)
async def api_create_appointment(data: AppointmentCreate):
    """Create a new appointment."""
    return await create_appointment(data)


@router.get("/appointments", response_model=List[Appointment])
async def api_list_appointments(
    location_id: str = Query(..., description="Location ID"),
    contact_id: Optional[str] = Query(None, description="Filter by contact"),
    status: Optional[AppointmentStatus] = Query(None, description="Filter by status"),
    start_after: Optional[datetime] = Query(None, description="Start time after"),
    start_before: Optional[datetime] = Query(None, description="Start time before"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0)
):
    """List appointments with optional filtering."""
    filter = AppointmentFilter(
        location_id=location_id,
        contact_id=contact_id,
        status=status,
        start_after=start_after,
        start_before=start_before,
        limit=limit,
        offset=offset
    )
    return await list_appointments(filter)


@router.get("/appointments/{appointment_id}", response_model=Appointment)
async def api_get_appointment(appointment_id: str):
    """Get an appointment by ID."""
    appt = await get_appointment(appointment_id)
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return appt


@router.patch("/appointments/{appointment_id}", response_model=Appointment)
async def api_update_appointment(appointment_id: str, data: AppointmentUpdate):
    """Update an appointment."""
    appt = await update_appointment(appointment_id, data)
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return appt


# ============================================
# TWILIO PHONE NUMBER MAPPING
# ============================================

@router.post("/twilio-numbers")
async def register_twilio_number_endpoint(
    phone_number: str,
    location_id: str,
    twilio_sid: Optional[str] = None,
    friendly_name: Optional[str] = None
):
    """Register a Twilio phone number for a location."""
    result = await register_twilio_number(phone_number, location_id, twilio_sid, friendly_name)
    return {"success": True, "data": result}


@router.get("/twilio-numbers/{location_id}")
async def list_twilio_numbers_endpoint(location_id: str):
    """List all Twilio numbers for a location."""
    numbers = await list_twilio_numbers_for_location(location_id)
    return {"success": True, "data": numbers}


@router.get("/twilio-numbers/lookup/{phone_number}")
async def lookup_twilio_number_endpoint(phone_number: str):
    """Look up which location owns a Twilio number."""
    location_id = await get_location_id_from_twilio_number(phone_number)
    if location_id:
        return {"success": True, "location_id": location_id}
    return {"success": False, "error": "Number not found"}


# ============================================
# OUTBOX ENDPOINTS
# ============================================

@router.get("/outbox/stats")
async def get_outbox_stats_endpoint():
    """
    Get outbox statistics for monitoring.

    Returns counts by status and oldest pending item age.
    """
    try:
        stats = await get_outbox_stats()
        return {"success": True, "data": stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/outbox/dead-letter")
async def get_dead_letter_endpoint(limit: int = Query(100, ge=1, le=1000)):
    """
    Get dead letter items for admin review.

    Args:
        limit: Maximum number of items to return (1-1000)
    """
    try:
        items = await get_dead_letter_items(limit=limit)
        return {"success": True, "count": len(items), "data": items}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/outbox/{outbox_id}/replay")
async def replay_outbox_endpoint(outbox_id: str):
    """
    Manually replay a failed/dead_letter outbox item.

    Resets the item to pending status with attempt_count=0.
    Used by admins to retry after fixing underlying issues.

    Args:
        outbox_id: UUID of the outbox item to replay
    """
    try:
        success = await replay_outbox_item(outbox_id)
        if success:
            return {"success": True, "message": f"Outbox item {outbox_id} queued for replay"}
        else:
            raise HTTPException(status_code=404, detail="Outbox item not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# UTILITY ENDPOINTS
# ============================================

@router.get("/health")
async def crm_health():
    """CRM module health check."""
    from modules.crm_core import get_pool
    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}
