"""
CRM-specific intents for natural language control.

Defines intents, entities, and patterns for parsing natural language commands.
"""

from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel


class CRMIntent(str, Enum):
    """CRM operation intents."""

    # Contact intents
    SEARCH_CONTACTS = "search_contacts"
    GET_CONTACT = "get_contact"
    CREATE_CONTACT = "create_contact"
    UPDATE_CONTACT = "update_contact"
    TAG_CONTACT = "tag_contact"
    UNTAG_CONTACT = "untag_contact"

    # Conversation intents
    LIST_CONVERSATIONS = "list_conversations"
    GET_CONVERSATION = "get_conversation"

    # Message intents
    SEND_SMS = "send_sms"
    SEND_BULK_SMS = "send_bulk_sms"

    # Appointment intents
    CREATE_APPOINTMENT = "create_appointment"
    LIST_APPOINTMENTS = "list_appointments"
    CANCEL_APPOINTMENT = "cancel_appointment"

    # Analytics intents
    GET_STATS = "get_stats"
    GET_ACTIVITY = "get_activity"

    # Unknown
    UNKNOWN = "unknown"


class CRMEntity(BaseModel):
    """Extracted entity from user input."""
    entity_type: str  # contact_name, phone, email, tag, date, time, etc.
    value: Any
    confidence: float = 1.0


class CRMCommand(BaseModel):
    """Parsed command ready for execution."""
    intent: CRMIntent
    entities: List[CRMEntity] = []
    raw_input: str
    confidence: float = 0.0


# Intent patterns for keyword matching (fast, no LLM needed)
INTENT_PATTERNS = {
    CRMIntent.SEARCH_CONTACTS: [
        "show me", "find", "search", "list contacts", "get contacts",
        "who", "contacts with", "leads from", "customers"
    ],
    CRMIntent.GET_CONTACT: [
        "get contact", "show contact", "contact details", "look up"
    ],
    CRMIntent.CREATE_CONTACT: [
        "create contact", "add contact", "new contact", "add lead"
    ],
    CRMIntent.UPDATE_CONTACT: [
        "update contact", "edit contact", "change contact", "modify"
    ],
    CRMIntent.TAG_CONTACT: [
        "tag", "add tag", "label", "mark as"
    ],
    CRMIntent.UNTAG_CONTACT: [
        "untag", "remove tag", "unlabel"
    ],
    CRMIntent.SEND_SMS: [
        "send", "text", "sms", "message"
    ],
    CRMIntent.SEND_BULK_SMS: [
        "send to all", "bulk", "mass text", "broadcast"
    ],
    CRMIntent.CREATE_APPOINTMENT: [
        "schedule", "book", "appointment", "meeting", "call with"
    ],
    CRMIntent.LIST_APPOINTMENTS: [
        "appointments", "schedule for", "calendar", "what's scheduled"
    ],
    CRMIntent.GET_STATS: [
        "stats", "statistics", "how many", "count", "total"
    ],
    CRMIntent.GET_ACTIVITY: [
        "activity", "recent", "what happened", "updates"
    ],
}

# Entity extraction patterns
ENTITY_PATTERNS = {
    "phone": r'\+?1?[-.\s]?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}',
    "email": r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
    "date_relative": r'(today|tomorrow|yesterday|this week|last week|next week)',
    "date_absolute": r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
    "time": r'(\d{1,2}:\d{2}\s*(?:am|pm)?|\d{1,2}\s*(?:am|pm))',
    "tag": r'tagged?\s+["\']?(\w+)["\']?|tag\s+["\']?(\w+)["\']?',
}
