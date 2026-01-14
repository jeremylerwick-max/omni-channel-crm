from fastapi import APIRouter, Request, Form, HTTPException, Depends
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from datetime import datetime
from app.core.database import get_db
from app.core.config import settings
from app.models import Message, Contact, Conversation
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

DEFAULT_ACCOUNT_ID = "00000000-0000-0000-0000-000000000001"

@router.post("/twilio/sms")
async def twilio_sms_webhook(
    request: Request,
    From: str = Form(...),
    To: str = Form(...),
    Body: str = Form(...),
    MessageSid: str = Form(...),
    AccountSid: str = Form(None),
    NumMedia: int = Form(0),
    db: AsyncSession = Depends(get_db)
):
    """
    Handle incoming SMS from Twilio.
    
    Twilio sends:
    - From: Sender phone number
    - To: Your Twilio number
    - Body: Message text
    - MessageSid: Unique message ID
    """
    logger.info(f"📥 Incoming SMS from {From}: {Body[:50]}...")
    
    # Normalize phone number
    phone = From.replace("+", "").replace("-", "").replace(" ", "")
    if phone.startswith("1") and len(phone) == 11:
        phone = phone[1:]
    
    # Find or create contact
    result = await db.execute(
        select(Contact).where(
            Contact.account_id == DEFAULT_ACCOUNT_ID,
            Contact.phone.contains(phone[-10:])
        )
    )
    contact = result.scalar_one_or_none()
    
    if not contact:
        # Create new contact from incoming SMS
        contact = Contact(
            account_id=DEFAULT_ACCOUNT_ID,
            phone=From,
            source="sms_inbound",
            sms_consent=True  # They texted us
        )
        db.add(contact)
        await db.flush()
        logger.info(f"Created new contact for {From}")
    
    # Handle opt-out keywords
    body_lower = Body.strip().lower()
    if body_lower in ["stop", "unsubscribe", "cancel", "quit", "end"]:
        contact.do_not_disturb = True
        contact.status = "unsubscribed"
        logger.info(f"Contact {contact.id} opted out")
        return Response(
            content='<?xml version="1.0" encoding="UTF-8"?><Response><Message>You have been unsubscribed. Reply START to resubscribe.</Message></Response>',
            media_type="application/xml"
        )
    
    # Handle opt-in keywords
    if body_lower in ["start", "yes", "unstop"]:
        contact.do_not_disturb = False
        contact.status = "active"
        contact.sms_consent = True
        logger.info(f"Contact {contact.id} re-subscribed")
    
    # Find or create conversation
    result = await db.execute(
        select(Conversation).where(
            Conversation.contact_id == contact.id,
            Conversation.channel == "sms"
        )
    )
    conversation = result.scalar_one_or_none()
    
    if not conversation:
        conversation = Conversation(
            account_id=DEFAULT_ACCOUNT_ID,
            contact_id=contact.id,
            channel="sms",
            status="open",
            ai_enabled=True
        )
        db.add(conversation)
        await db.flush()
    
    # Store the inbound message
    message = Message(
        account_id=DEFAULT_ACCOUNT_ID,
        contact_id=contact.id,
        conversation_id=conversation.id,
        channel="sms",
        direction="inbound",
        status="delivered",
        from_address=From,
        to_address=To,
        body=Body,
        provider="twilio",
        provider_id=MessageSid
    )
    db.add(message)
    
    # Update conversation
    conversation.last_message_at = datetime.utcnow()
    conversation.last_message_preview = Body[:255]
    conversation.unread_count += 1
    
    # Update contact
    contact.last_contacted_at = datetime.utcnow()
    
    await db.flush()
    
    # TODO: Trigger AI response if ai_enabled
    # TODO: Trigger workflow if configured
    
    # Return empty TwiML (no auto-response for now)
    return Response(
        content='<?xml version="1.0" encoding="UTF-8"?><Response></Response>',
        media_type="application/xml"
    )

@router.post("/twilio/status")
async def twilio_status_webhook(
    MessageSid: str = Form(...),
    MessageStatus: str = Form(...),
    ErrorCode: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db)
):
    """Handle Twilio message status callbacks."""
    logger.info(f"📊 Message {MessageSid} status: {MessageStatus}")
    
    result = await db.execute(
        select(Message).where(Message.provider_id == MessageSid)
    )
    message = result.scalar_one_or_none()
    
    if message:
        message.provider_status = MessageStatus
        if MessageStatus == "delivered":
            message.status = "delivered"
            message.delivered_at = datetime.utcnow()
        elif MessageStatus == "failed":
            message.status = "failed"
    
    return {"received": True}

@router.post("/sendgrid/events")
async def sendgrid_events_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """Handle SendGrid email events (opens, clicks, bounces)."""
    events = await request.json()
    for event in events:
        logger.info(f"📧 Email event: {event.get('event')} for {event.get('email')}")
        # TODO: Update message status based on event type
    return {"received": True, "count": len(events)}

@router.post("/stripe")
async def stripe_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """Handle Stripe webhooks (subscriptions, payments)."""
    payload = await request.body()
    # TODO: Verify Stripe signature and process events
    logger.info("💳 Stripe webhook received")
    return {"received": True}
