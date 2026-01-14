"""
Twilio Webhook Handlers

FastAPI router for handling inbound SMS and status callbacks from Twilio.
"""

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import PlainTextResponse
import logging
import os

from modules.twilio_sms.executor import TwilioSMSExecutor
from modules.twilio_sms.models import SendSMSRequest
from modules.crm_core import (
    find_contact_by_phone,
    create_contact,
    get_or_create_conversation,
    create_message,
    update_message_status,
    get_conversation_messages,
    update_message,
    get_location,
    get_location_id_from_twilio_number,
    update_contact,
    update_conversation_status,
    add_tag_to_contact,
    cancel_pending_outbox_for_contact,
    ContactCreate,
    ContactUpdate,
    MessageCreate
)
from modules.ai_conversation import (
    AIConversationExecutor,
    ConversationContext
)
from modules.compliance import is_optout, is_optin

router = APIRouter(prefix="/webhooks/twilio", tags=["Twilio Webhooks"])
logger = logging.getLogger(__name__)

# Routing safety flag - default false for production safety
ALLOW_TWILIO_FALLBACK_ROUTING = os.getenv("ALLOW_TWILIO_FALLBACK_ROUTING", "false").lower() == "true"


@router.post("/inbound")
async def handle_inbound_sms(request: Request):
    """
    Handle inbound SMS from Twilio webhook.

    Flow:
    1. Parse webhook data
    2. Find or create contact by phone number
    3. Find or create conversation
    4. Create message record
    5. Return empty TwiML response
    """
    try:
        form_data = await request.form()
        data = dict(form_data)

        logger.info(f"Inbound SMS webhook: {data.get('From')} -> {data.get('To')}")

        # Parse webhook data
        twilio = TwilioSMSExecutor()
        parsed = twilio.parse_webhook(data)

        from_number = parsed["from_number"]
        to_number = parsed["to_number"]
        body = parsed["body"]
        message_sid = parsed["message_sid"]

        logger.info(f"Message: {body[:100]}")

        # Map Twilio 'To' number to location_id
        location_id = await get_location_id_from_twilio_number(to_number)

        if not location_id:
            # Unknown Twilio number - structured error logging
            logger.error(
                "ROUTING_FAILURE: Unknown Twilio number",
                extra={
                    "event": "routing_failure",
                    "twilio_to": to_number,
                    "twilio_from": from_number,
                    "message_sid": message_sid,
                    "fallback_allowed": ALLOW_TWILIO_FALLBACK_ROUTING
                }
            )

            if not ALLOW_TWILIO_FALLBACK_ROUTING:
                # Production mode: reject message immediately (no DB writes)
                logger.error(
                    "REJECTED: Inbound SMS to unknown number",
                    extra={
                        "event": "message_rejected",
                        "reason": "unknown_twilio_number",
                        "twilio_to": to_number,
                        "twilio_from": from_number,
                        "message_sid": message_sid
                    }
                )
                return PlainTextResponse(
                    content='<?xml version="1.0" encoding="UTF-8"?><Response></Response>',
                    media_type="application/xml"
                )

            # Development mode: allow fallback
            logger.warning(
                "FALLBACK_ROUTING: Using default location",
                extra={
                    "event": "fallback_routing",
                    "twilio_to": to_number,
                    "default_location": "00000000-0000-0000-0000-000000000001"
                }
            )
            location_id = "00000000-0000-0000-0000-000000000001"

        # Find or create contact by phone
        contact = await find_contact_by_phone(from_number, location_id)

        if not contact:
            logger.info(f"Creating new contact for {from_number}")
            # Create new contact from inbound SMS
            contact_data = ContactCreate(
                location_id=location_id,
                phone=from_number,
                source="inbound_sms"
            )
            contact = await create_contact(contact_data)

        # Find or create conversation
        conversation = await get_or_create_conversation(
            location_id=location_id,
            contact_id=contact.id,
            channel="sms"
        )

        # Create message record
        message_data = MessageCreate(
            conversation_id=conversation.id,
            contact_id=contact.id,
            channel="sms",
            direction="inbound",
            body=body,
            status="received",
            external_id=message_sid,
            media_urls=parsed.get("media_urls", [])
        )
        message = await create_message(message_data)

        logger.info(f"Inbound SMS processed successfully. Message ID: {message.id}")

        # ============================================================
        # DETERMINISTIC OPT-OUT DETECTION (BEFORE AI PROCESSING)
        # ============================================================
        # Check for opt-out FIRST - this is a compliance requirement.
        # Must be deterministic (no AI involved).
        if is_optout(body):
            logger.warning(f"OPT_OUT detected from contact {contact.id} ({from_number}): '{body[:50]}'")

            # Determine if this is the first opt-out (to avoid duplicate confirmations)
            is_first_optout = not contact.dnd and (not contact.tags or "opted_out" not in contact.tags)

            # ============================================================
            # STEP 1: Send confirmation BEFORE setting DND (only on first opt-out)
            # This avoids any bypass loopholes in the DND gate
            # ============================================================
            if is_first_optout:
                confirmation_body = "You have been unsubscribed. Reply START to resubscribe."
                try:
                    confirm_request = SendSMSRequest(
                        to=from_number,
                        body=confirmation_body,
                        location_id=location_id,
                        contact_id=str(contact.id),  # Use real contact_id - DND not set yet
                        conversation_id=str(conversation.id)
                    )
                    twilio = TwilioSMSExecutor()
                    confirm_response = await twilio.send_sms(confirm_request)

                    if confirm_response.success:
                        logger.info(f"Opt-out confirmation sent: {confirm_response.message_sid}")
                        # Record the confirmation message
                        confirm_message = MessageCreate(
                            conversation_id=conversation.id,
                            contact_id=contact.id,
                            channel="sms",
                            direction="outbound",
                            body=confirmation_body,
                            status="queued",
                            external_id=confirm_response.message_sid
                        )
                        await create_message(confirm_message)
                    else:
                        logger.error(f"Failed to send opt-out confirmation: {confirm_response.error}")
                except Exception as e:
                    logger.exception(f"Error sending opt-out confirmation: {e}")
            else:
                logger.info(f"Skipping opt-out confirmation (already DND or opted_out tag present)")

            # ============================================================
            # STEP 2: NOW set DND and close everything (AFTER confirmation sent)
            # ============================================================

            # Set DND flag on contact
            contact_update = ContactUpdate(dnd=True)
            await update_contact(contact.id, contact_update)
            logger.info(f"Contact {contact.id} DND set to TRUE")

            # Close the conversation
            await update_conversation_status(str(conversation.id), "closed")
            logger.info(f"Conversation {conversation.id} closed due to opt-out")

            # Add "opted_out" tag
            await add_tag_to_contact(str(contact.id), "opted_out", "system")
            logger.info(f"Tag 'opted_out' added to contact {contact.id}")

            # Cancel any pending outbox items for this contact
            cancelled_count = await cancel_pending_outbox_for_contact(str(contact.id))
            if cancelled_count > 0:
                logger.info(f"Cancelled {cancelled_count} pending outbox items for contact {contact.id}")

            # Return early - no AI processing for opt-outs
            return PlainTextResponse(
                content='<?xml version="1.0" encoding="UTF-8"?><Response></Response>',
                media_type="application/xml"
            )

        # Check for opt-in (resubscribe) - only if contact is currently DND
        if is_optin(body) and contact.dnd:
            logger.info(f"OPT_IN detected from DND contact {contact.id} ({from_number}): '{body[:50]}'")

            # Clear DND flag
            contact_update = ContactUpdate(dnd=False)
            await update_contact(contact.id, contact_update)
            logger.info(f"Contact {contact.id} DND set to FALSE (resubscribed)")

            # Add "opted_in" tag
            await add_tag_to_contact(str(contact.id), "opted_in", "system")

            # Reopen conversation if closed
            if conversation.status == "closed":
                await update_conversation_status(str(conversation.id), "open")
                logger.info(f"Conversation {conversation.id} reopened due to opt-in")

            # Send confirmation
            optin_body = "Welcome back! You have been resubscribed to messages."
            try:
                optin_request = SendSMSRequest(
                    to=from_number,
                    body=optin_body,
                    location_id=location_id,
                    contact_id=str(contact.id),
                    conversation_id=str(conversation.id)
                )
                twilio = TwilioSMSExecutor()
                optin_response = await twilio.send_sms(optin_request)

                if optin_response.success:
                    logger.info(f"Opt-in confirmation sent: {optin_response.message_sid}")
                    optin_message = MessageCreate(
                        conversation_id=conversation.id,
                        contact_id=contact.id,
                        channel="sms",
                        direction="outbound",
                        body=optin_body,
                        status="queued",
                        external_id=optin_response.message_sid
                    )
                    await create_message(optin_message)
                else:
                    logger.error(f"Failed to send opt-in confirmation: {optin_response.error}")
            except Exception as e:
                logger.exception(f"Error sending opt-in confirmation: {e}")

            # Return early - no AI processing for opt-ins
            return PlainTextResponse(
                content='<?xml version="1.0" encoding="UTF-8"?><Response></Response>',
                media_type="application/xml"
            )

        # ============================================================
        # END OPT-OUT/OPT-IN DETECTION
        # ============================================================

        # Check if AI is enabled for this location
        location = await get_location(location_id)
        ai_enabled = location.settings.get("ai_enabled", False) if location.settings else False

        if ai_enabled:
            try:
                # Generate AI response
                ai_executor = AIConversationExecutor()

                # Get conversation history
                recent_messages = await get_conversation_messages(conversation.id, limit=10)

                # Build conversation context
                context = ConversationContext(
                    contact_id=contact.id,
                    contact_name=contact.first_name,
                    conversation_id=conversation.id,
                    recent_messages=recent_messages,
                    contact_tags=contact.tags or [],
                    location_name=location.name if location else None,
                    location_timezone=location.timezone if location else "America/Chicago"
                )

                # Generate AI response
                ai_response = await ai_executor.generate_response(context, body)

                logger.info(f"AI response generated: {ai_response.reply_text[:50]}...")

                # Update inbound message with AI metadata
                await update_message(
                    message_id=message.id,
                    ai_intent=ai_response.intent.value,
                    ai_sentiment=ai_response.sentiment.value,
                    ai_confidence=ai_response.confidence
                )

                # Send AI reply via Twilio
                sms_request = SendSMSRequest(
                    to=from_number,
                    body=ai_response.reply_text,
                    location_id=location_id,
                    contact_id=contact.id,
                    conversation_id=conversation.id
                )

                twilio_response = await twilio.send_sms(sms_request)

                if twilio_response.success:
                    # Create outbound message record
                    outbound_message = MessageCreate(
                        conversation_id=conversation.id,
                        contact_id=contact.id,
                        channel="sms",
                        direction="outbound",
                        body=ai_response.reply_text,
                        status="queued",
                        external_id=twilio_response.message_sid,
                        ai_intent=ai_response.intent.value,
                        ai_sentiment=ai_response.sentiment.value,
                        ai_confidence=ai_response.confidence
                    )
                    await create_message(outbound_message)

                    logger.info(f"AI reply sent successfully. SID: {twilio_response.message_sid}")
                else:
                    logger.error(f"Failed to send AI reply: {twilio_response.error}")

            except Exception as ai_error:
                logger.exception(f"Error generating/sending AI response: {str(ai_error)}")
                # Continue without AI response

        # Return empty TwiML response
        return PlainTextResponse(
            content='<?xml version="1.0" encoding="UTF-8"?><Response></Response>',
            media_type="application/xml"
        )

    except Exception as e:
        logger.exception(f"Error handling inbound SMS: {str(e)}")
        # Still return 200 OK to Twilio to avoid retries
        return PlainTextResponse(
            content='<?xml version="1.0" encoding="UTF-8"?><Response></Response>',
            media_type="application/xml"
        )


@router.post("/status")
async def handle_status_callback(request: Request):
    """
    Handle message status updates from Twilio webhook.

    Updates message status: queued -> sent -> delivered (or failed)
    """
    try:
        form_data = await request.form()
        data = dict(form_data)

        message_sid = data.get("MessageSid")
        status = data.get("MessageStatus")
        error_message = data.get("ErrorMessage")

        logger.info(f"Status update: {message_sid} -> {status}")

        if error_message:
            logger.warning(f"Message {message_sid} error: {error_message}")

        # Update message status by external_id
        updated = await update_message_status(
            external_id=message_sid,
            status=status,
            error_message=error_message
        )

        if updated:
            logger.info(f"Message status updated successfully")
        else:
            logger.warning(f"Message not found for SID: {message_sid}")

        return {"status": "ok"}

    except Exception as e:
        logger.exception(f"Error handling status callback: {str(e)}")
        return {"status": "error", "message": str(e)}


@router.get("/health")
async def twilio_health():
    """Health check for Twilio webhooks"""
    return {"status": "healthy", "service": "twilio_webhooks"}
