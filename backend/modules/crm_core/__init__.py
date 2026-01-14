"""
Ziloss CRM Core Module

Provides core CRM functionality including:
- Contacts management
- Conversations and messages
- Appointments
- Tags
"""

from .models import (
    # Enums
    ContactType, ConversationStatus, MessageDirection, 
    MessageStatus, AppointmentStatus, Channel,
    
    # Location
    Location, LocationCreate,
    
    # Contact
    Contact, ContactCreate, ContactUpdate, ContactFilter,
    
    # Tag
    Tag, TagCreate,
    
    # Conversation
    Conversation, ConversationCreate, ConversationFilter, ConversationWithContact,
    
    # Message
    Message, MessageCreate,
    
    # Appointment
    Appointment, AppointmentCreate, AppointmentUpdate, AppointmentFilter,
)

from .executor import (
    execute,
    get_pool, close_pool,

    # Location
    create_location, get_location, list_locations,

    # Contact
    create_contact, get_contact, update_contact, delete_contact, list_contacts,
    add_tag_to_contact, remove_tag_from_contact, find_contact_by_phone,

    # Tag
    create_tag, get_tag, get_tag_by_name, list_tags,

    # Conversation
    create_conversation, get_conversation, get_or_create_conversation, list_conversations,
    update_conversation_status,

    # Message
    create_message, get_message, list_messages, update_message_status,
    get_conversation_messages, update_message,

    # Appointment
    create_appointment, get_appointment, update_appointment, list_appointments,

    # Twilio Phone Number Mapping
    normalize_phone_e164, get_location_id_from_twilio_number,
    register_twilio_number, list_twilio_numbers_for_location,
)

from .outbox import (
    enqueue_outbox, get_pending_outbox_items, mark_outbox_sending,
    mark_outbox_sent, mark_outbox_failed, get_outbox_stats,
    replay_outbox_item, get_dead_letter_items, cancel_pending_outbox_for_contact,
    OutboxStatus, OutboxObjectType
)

__all__ = [
    'execute',
    'get_pool', 'close_pool',

    # Enums
    'ContactType', 'ConversationStatus', 'MessageDirection',
    'MessageStatus', 'AppointmentStatus', 'Channel',

    # Location
    'Location', 'LocationCreate',
    'create_location', 'get_location', 'list_locations',

    # Contact
    'Contact', 'ContactCreate', 'ContactUpdate', 'ContactFilter',
    'create_contact', 'get_contact', 'update_contact', 'delete_contact', 'list_contacts',
    'add_tag_to_contact', 'remove_tag_from_contact', 'find_contact_by_phone',

    # Tag
    'Tag', 'TagCreate',
    'create_tag', 'get_tag', 'get_tag_by_name', 'list_tags',

    # Conversation
    'Conversation', 'ConversationCreate', 'ConversationFilter', 'ConversationWithContact',
    'create_conversation', 'get_conversation', 'get_or_create_conversation', 'list_conversations',
    'update_conversation_status',

    # Message
    'Message', 'MessageCreate',
    'create_message', 'get_message', 'list_messages', 'update_message_status',
    'get_conversation_messages', 'update_message',

    # Appointment
    'Appointment', 'AppointmentCreate', 'AppointmentUpdate', 'AppointmentFilter',
    'create_appointment', 'get_appointment', 'update_appointment', 'list_appointments',

    # Twilio Phone Number Mapping
    'normalize_phone_e164', 'get_location_id_from_twilio_number',
    'register_twilio_number', 'list_twilio_numbers_for_location',

    # Transactional Outbox
    'enqueue_outbox', 'get_pending_outbox_items', 'mark_outbox_sending',
    'mark_outbox_sent', 'mark_outbox_failed', 'get_outbox_stats',
    'replay_outbox_item', 'get_dead_letter_items', 'cancel_pending_outbox_for_contact',
    'OutboxStatus', 'OutboxObjectType',
]

__version__ = '1.0.0'
