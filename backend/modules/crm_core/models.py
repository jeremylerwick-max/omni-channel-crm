"""
Ziloss CRM Core - Pydantic Models
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
import re


class ContactType(str, Enum):
    LEAD = "lead"
    CUSTOMER = "customer"
    VENDOR = "vendor"


class ConversationStatus(str, Enum):
    OPEN = "open"
    CLOSED = "closed"
    SNOOZED = "snoozed"
    PENDING = "pending"


class MessageDirection(str, Enum):
    INBOUND = "inbound"
    OUTBOUND = "outbound"


class MessageStatus(str, Enum):
    RECEIVED = "received"  # For inbound messages
    QUEUED = "queued"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"


class AppointmentStatus(str, Enum):
    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"


class Channel(str, Enum):
    SMS = "sms"
    EMAIL = "email"
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"
    WHATSAPP = "whatsapp"
    WEBCHAT = "webchat"
    PHONE = "phone"


# ============================================
# LOCATION MODELS
# ============================================

class LocationBase(BaseModel):
    name: str
    slug: str
    timezone: str = "America/Chicago"
    phone: Optional[str] = None
    email: Optional[str] = None
    address1: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: str = "US"
    settings: Dict[str, Any] = {}
    business_hours: Dict[str, Any] = {}


class LocationCreate(LocationBase):
    pass


class Location(LocationBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================
# TAG MODELS
# ============================================

class TagBase(BaseModel):
    name: str
    color: str = "#3B82F6"


class TagCreate(TagBase):
    location_id: str


class Tag(TagBase):
    id: str
    location_id: str
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================
# CONTACT MODELS
# ============================================

class ContactBase(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address1: Optional[str] = None
    address2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: str = "US"
    company_name: Optional[str] = None
    website: Optional[str] = None
    source: Optional[str] = None
    medium: Optional[str] = None
    assigned_to: Optional[str] = None
    type: ContactType = ContactType.LEAD
    dnd: bool = False
    dnd_settings: Dict[str, Any] = {}
    custom_fields: Dict[str, Any] = {}

    @field_validator('phone')
    @classmethod
    def normalize_phone(cls, v):
        if v:
            # Remove all non-digit characters except +
            cleaned = re.sub(r'[^\d+]', '', v)
            return cleaned
        return v


class ContactCreate(ContactBase):
    location_id: str


class ContactUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address1: Optional[str] = None
    address2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    company_name: Optional[str] = None
    website: Optional[str] = None
    source: Optional[str] = None
    medium: Optional[str] = None
    assigned_to: Optional[str] = None
    type: Optional[ContactType] = None
    dnd: Optional[bool] = None
    dnd_settings: Optional[Dict[str, Any]] = None
    custom_fields: Optional[Dict[str, Any]] = None


class Contact(ContactBase):
    id: str
    location_id: str
    created_at: datetime
    updated_at: datetime
    last_contacted_at: Optional[datetime] = None
    tags: List[str] = []  # Tag names

    class Config:
        from_attributes = True


# ============================================
# CONVERSATION MODELS
# ============================================

class ConversationBase(BaseModel):
    channel: Channel = Channel.SMS
    channel_id: Optional[str] = None
    status: ConversationStatus = ConversationStatus.OPEN
    assigned_to: Optional[str] = None


class ConversationCreate(ConversationBase):
    location_id: str
    contact_id: str


class Conversation(ConversationBase):
    id: str
    location_id: str
    contact_id: str
    unread_count: int = 0
    last_message_body: Optional[str] = None
    last_message_direction: Optional[str] = None
    last_message_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ConversationWithContact(Conversation):
    contact: Optional[Contact] = None


# ============================================
# MESSAGE MODELS
# ============================================

class MessageBase(BaseModel):
    direction: MessageDirection
    body: Optional[str] = None
    media_urls: List[str] = []
    channel: Channel = Channel.SMS
    external_id: Optional[str] = None
    status: MessageStatus = MessageStatus.SENT
    ai_generated: bool = False
    ai_model: Optional[str] = None
    sentiment: Optional[str] = None
    intent: Optional[str] = None


class MessageCreate(MessageBase):
    conversation_id: str
    contact_id: str


class Message(MessageBase):
    id: str
    conversation_id: str
    contact_id: str
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    delivered_at: Optional[datetime] = None
    read_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============================================
# APPOINTMENT MODELS
# ============================================

class AppointmentBase(BaseModel):
    title: str
    description: Optional[str] = None
    start_time: datetime
    end_time: datetime
    timezone: str = "America/Chicago"
    status: AppointmentStatus = AppointmentStatus.SCHEDULED
    location: Optional[str] = None
    assigned_to: Optional[str] = None
    notes: Optional[str] = None
    calendar_id: Optional[str] = None
    external_id: Optional[str] = None


class AppointmentCreate(AppointmentBase):
    location_id: str
    contact_id: str


class AppointmentUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    timezone: Optional[str] = None
    status: Optional[AppointmentStatus] = None
    location: Optional[str] = None
    assigned_to: Optional[str] = None
    notes: Optional[str] = None


class Appointment(AppointmentBase):
    id: str
    location_id: str
    contact_id: str
    reminder_sent: bool = False
    reminder_sent_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================
# QUERY/FILTER MODELS
# ============================================

class ContactFilter(BaseModel):
    location_id: str
    search: Optional[str] = None  # Search in name, email, phone
    tag: Optional[str] = None
    type: Optional[ContactType] = None
    dnd: Optional[bool] = None
    source: Optional[str] = None
    limit: int = 100
    offset: int = 0


class ConversationFilter(BaseModel):
    location_id: str
    contact_id: Optional[str] = None
    status: Optional[ConversationStatus] = None
    channel: Optional[Channel] = None
    limit: int = 100
    offset: int = 0


class AppointmentFilter(BaseModel):
    location_id: str
    contact_id: Optional[str] = None
    status: Optional[AppointmentStatus] = None
    start_after: Optional[datetime] = None
    start_before: Optional[datetime] = None
    limit: int = 100
    offset: int = 0
