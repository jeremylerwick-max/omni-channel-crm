"""
Twilio SMS Executor

Handles sending SMS via Twilio and parsing webhook data.
"""

import os
import logging
from typing import Dict, Any, List
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

from .models import SendSMSRequest, SendSMSResponse, MessageStatus

logger = logging.getLogger(__name__)


class TwilioSMSExecutor:
    """Twilio SMS client for sending messages and parsing webhooks"""

    def __init__(self):
        """Initialize Twilio client with credentials from environment variables"""
        self.account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        self.auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        self.from_number = os.getenv("TWILIO_PHONE_NUMBER")

        if not all([self.account_sid, self.auth_token, self.from_number]):
            logger.warning("Twilio credentials not fully configured in environment variables")
            self.client = None
        else:
            self.client = Client(self.account_sid, self.auth_token)
            logger.info(f"Twilio client initialized with phone number: {self.from_number}")

    async def send_sms(self, request: SendSMSRequest) -> SendSMSResponse:
        """
        Send SMS via Twilio with DND enforcement.

        CRITICAL SAFETY PROPERTY: DND=true MUST block ALL sends. No exceptions.

        Args:
            request: SendSMSRequest with to, body, location_id

        Returns:
            SendSMSResponse with success status and message_sid
        """
        if not self.client:
            return SendSMSResponse(
                success=False,
                error="Twilio client not configured. Check environment variables."
            )

        # ============================================================
        # CONTACT LOOKUP (Required for DND + Quiet Hours)
        # ============================================================
        from modules.crm_core import get_contact, find_contact_by_phone
        
        contact = None
        
        # Try to get contact by ID first
        if request.contact_id:
            contact = await get_contact(request.contact_id)
        
        # If no contact_id or contact not found, try phone lookup
        if not contact and request.to and request.location_id:
            contact = await find_contact_by_phone(request.to, request.location_id)

        # ============================================================
        # DND ENFORCEMENT GATE (NON-NEGOTIABLE)
        # ============================================================
        # This check MUST happen before ANY Twilio API call.
        # If contact has DND=true, we MUST NOT send. Period.
        if contact:
            # Check global DND flag
            if contact.dnd:
                logger.warning(
                    f"DND_BLOCK: Attempted SMS to DND contact {contact.id} "
                    f"(phone: {request.to})"
                )
                return SendSMSResponse(
                    success=False,
                    error="Contact is on Do Not Disturb list",
                    blocked_reason="dnd"
                )

            # Check channel-specific DND (if dnd_settings exists)
            if hasattr(contact, 'dnd_settings') and contact.dnd_settings:
                if isinstance(contact.dnd_settings, dict) and contact.dnd_settings.get("sms", False):
                    logger.warning(
                        f"DND_BLOCK: Contact {contact.id} has SMS-specific DND "
                        f"(phone: {request.to})"
                    )
                    return SendSMSResponse(
                        success=False,
                        error="Contact has SMS Do Not Disturb",
                        blocked_reason="dnd_sms"
                    )
        # ============================================================
        # END DND GATE
        # ============================================================

        # ============================================================
        # QUIET HOURS CHECK
        # ============================================================
        # Check if message should be deferred due to quiet hours (9 PM - 8 AM local time)
        from modules.compliance import (
            get_contact_timezone,
            is_quiet_hours,
            get_next_send_time
        )

        # Get contact timezone (uses phone area code as fallback)
        contact_tz, tz_source = get_contact_timezone(
            contact.timezone if contact and hasattr(contact, 'timezone') else None,
            contact.phone if contact else request.to,
            None  # location_tz - could be fetched from location if needed
        )

        # Check if currently in quiet hours
        if is_quiet_hours(contact_tz):
            next_send = get_next_send_time(contact_tz)
            logger.info(
                f"QUIET_HOURS: Blocking SMS to {request.to} in timezone {contact_tz} "
                f"(source: {tz_source}). Deferred until {next_send.isoformat()}"
            )
            return SendSMSResponse(
                success=False,
                error=f"Quiet hours active. Message deferred until {next_send.strftime('%Y-%m-%d %I:%M %p %Z')}",
                blocked_reason="quiet_hours",
                deferred_until=next_send
            )
        # ============================================================
        # END QUIET HOURS CHECK
        # ============================================================

        try:
            logger.info(f"Sending SMS to {request.to}: {request.body[:50]}...")

            # Get status callback URL from environment if available
            status_callback = os.getenv("TWILIO_STATUS_CALLBACK_URL")

            message_params = {
                "body": request.body,
                "from_": self.from_number,
                "to": request.to
            }

            if status_callback:
                message_params["status_callback"] = status_callback

            message = self.client.messages.create(**message_params)

            logger.info(f"SMS sent successfully. SID: {message.sid}, Status: {message.status}")

            return SendSMSResponse(
                success=True,
                message_sid=message.sid
            )

        except TwilioRestException as e:
            logger.error(f"Twilio error sending SMS: {e.msg} (code: {e.code})")
            return SendSMSResponse(
                success=False,
                error=f"Twilio error: {e.msg}"
            )

        except Exception as e:
            logger.exception(f"Unexpected error sending SMS: {str(e)}")
            return SendSMSResponse(
                success=False,
                error=f"Error: {str(e)}"
            )

    def parse_webhook(self, form_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse Twilio webhook form data

        Args:
            form_data: Dictionary of form data from Twilio webhook

        Returns:
            Dictionary with parsed webhook data
        """
        # Parse media URLs if present
        media_urls = []
        num_media = int(form_data.get("NumMedia", 0))

        for i in range(num_media):
            media_url = form_data.get(f"MediaUrl{i}")
            if media_url:
                media_urls.append(media_url)

        parsed = {
            "message_sid": form_data.get("MessageSid"),
            "from_number": form_data.get("From"),
            "to_number": form_data.get("To"),
            "body": form_data.get("Body", ""),
            "num_media": num_media,
            "media_urls": media_urls,
            "status": form_data.get("MessageStatus"),
            "account_sid": form_data.get("AccountSid"),
            "error_code": form_data.get("ErrorCode"),
            "error_message": form_data.get("ErrorMessage"),
        }

        return parsed
