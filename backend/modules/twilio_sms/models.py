"""
Twilio SMS Models

Pydantic models for Twilio SMS integration.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class MessageDirection(str, Enum):
    """Message direction enum"""
    INBOUND = "inbound"
    OUTBOUND = "outbound"


class MessageStatus(str, Enum):
    """Message status enum"""
    QUEUED = "queued"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    RECEIVED = "received"


class SendSMSRequest(BaseModel):
    """Request model for sending SMS"""
    to: str = Field(..., description="Phone number in E.164 format: +15551234567")
    body: str = Field(..., description="Message body text")
    location_id: str = Field(..., description="Location ID")
    contact_id: Optional[str] = Field(None, description="Contact ID (optional)")
    conversation_id: Optional[str] = Field(None, description="Conversation ID (optional)")


class SendSMSResponse(BaseModel):
    """Response model for sending SMS"""
    success: bool
    message_sid: Optional[str] = None
    error: Optional[str] = None
    blocked_reason: Optional[str] = None  # "dnd", "dnd_sms", "quiet_hours", etc.
    deferred_until: Optional[datetime] = None  # UTC datetime when message will be sent


class InboundSMS(BaseModel):
    """Model for inbound SMS from Twilio webhook"""
    from_number: str = Field(..., description="Sender phone number")
    to_number: str = Field(..., description="Recipient phone number (our Twilio number)")
    body: str = Field(..., description="Message body")
    message_sid: str = Field(..., description="Twilio message SID")
    num_media: int = Field(0, description="Number of media attachments")
    media_urls: List[str] = Field(default_factory=list, description="URLs of media attachments")
