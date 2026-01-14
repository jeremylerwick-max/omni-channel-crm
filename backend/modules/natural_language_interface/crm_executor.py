"""
Executes CRM commands parsed from natural language.

Translates parsed commands into actual CRM operations.
"""

import logging
from typing import Any, Dict, Optional
from datetime import datetime, timedelta

from .crm_intents import CRMIntent, CRMCommand, CRMEntity
from modules.crm_core import (
    list_contacts, get_contact, create_contact, update_contact,
    add_tag_to_contact, remove_tag_from_contact, find_contact_by_phone,
    list_conversations, get_conversation,
    create_appointment, list_appointments,
    ContactFilter, ContactCreate, AppointmentCreate, AppointmentStatus
)
from modules.twilio_sms import TwilioSMSExecutor, SendSMSRequest

logger = logging.getLogger(__name__)


class CRMCommandExecutor:
    """Executes parsed CRM commands."""

    def __init__(self, location_id: str):
        self.location_id = location_id
        self.twilio = TwilioSMSExecutor()

    async def execute(self, command: CRMCommand) -> Dict[str, Any]:
        """
        Execute a CRM command.

        Args:
            command: Parsed CRMCommand

        Returns:
            Dict with results or error
        """
        if command.confidence < 0.4:
            return {
                "success": False,
                "error": "I'm not sure what you want to do. Could you rephrase that?",
                "suggestions": self._get_suggestions(command)
            }

        try:
            handler = self._get_handler(command.intent)
            if handler:
                return await handler(command)
            else:
                return {
                    "success": False,
                    "error": f"I don't know how to handle: {command.intent}"
                }
        except Exception as e:
            logger.exception(f"Error executing command: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def _get_handler(self, intent: CRMIntent):
        """Get handler function for intent."""
        handlers = {
            CRMIntent.SEARCH_CONTACTS: self._handle_search_contacts,
            CRMIntent.GET_CONTACT: self._handle_get_contact,
            CRMIntent.CREATE_CONTACT: self._handle_create_contact,
            CRMIntent.TAG_CONTACT: self._handle_tag_contact,
            CRMIntent.SEND_SMS: self._handle_send_sms,
            CRMIntent.CREATE_APPOINTMENT: self._handle_create_appointment,
            CRMIntent.LIST_APPOINTMENTS: self._handle_list_appointments,
            CRMIntent.GET_STATS: self._handle_get_stats,
        }
        return handlers.get(intent)

    def _get_entity(self, command: CRMCommand, entity_type: str) -> Optional[Any]:
        """Get entity value by type."""
        for entity in command.entities:
            if entity.entity_type == entity_type:
                return entity.value
        return None

    async def _handle_search_contacts(self, command: CRMCommand) -> Dict[str, Any]:
        """Handle contact search."""
        # Build filter from entities
        filter_params = {"location_id": self.location_id}

        tag = self._get_entity(command, "tag")
        if tag:
            filter_params["tags"] = [tag]

        date = self._get_entity(command, "date_relative") or self._get_entity(command, "date_absolute")
        if date:
            filter_params["created_after"] = date

        contacts = await list_contacts(ContactFilter(**filter_params))

        return {
            "success": True,
            "count": len(contacts),
            "contacts": [self._contact_to_dict(c) for c in contacts[:20]],  # Limit to 20
            "message": f"Found {len(contacts)} contact(s)"
        }

    async def _handle_get_contact(self, command: CRMCommand) -> Dict[str, Any]:
        """Handle get single contact."""
        phone = self._get_entity(command, "phone")
        name = self._get_entity(command, "name")

        if phone:
            contact = await find_contact_by_phone(phone, self.location_id)
        elif name:
            # Search by name
            contacts = await list_contacts(ContactFilter(
                location_id=self.location_id,
                search=name
            ))
            contact = contacts[0] if contacts else None
        else:
            return {"success": False, "error": "Please specify a name or phone number"}

        if contact:
            return {"success": True, "contact": self._contact_to_dict(contact)}
        return {"success": False, "error": "Contact not found"}

    async def _handle_create_contact(self, command: CRMCommand) -> Dict[str, Any]:
        """Handle create contact."""
        name = self._get_entity(command, "name")
        phone = self._get_entity(command, "phone")
        email = self._get_entity(command, "email")

        if not phone and not email:
            return {"success": False, "error": "Please provide a phone number or email"}

        contact_data = ContactCreate(
            location_id=self.location_id,
            first_name=name or "Unknown",
            phone=phone,
            email=email
        )

        contact = await create_contact(contact_data)

        return {
            "success": True,
            "contact": self._contact_to_dict(contact),
            "message": f"Created contact: {name or phone}"
        }

    async def _handle_tag_contact(self, command: CRMCommand) -> Dict[str, Any]:
        """Handle tagging a contact."""
        phone = self._get_entity(command, "phone")
        name = self._get_entity(command, "name")
        tag = self._get_entity(command, "tag")

        if not tag:
            return {"success": False, "error": "What tag should I add?"}

        # Find contact
        contact = None
        if phone:
            contact = await find_contact_by_phone(phone, self.location_id)
        elif name:
            contacts = await list_contacts(ContactFilter(
                location_id=self.location_id,
                search=name
            ))
            contact = contacts[0] if contacts else None

        if not contact:
            return {"success": False, "error": "Contact not found"}

        await add_tag_to_contact(str(contact.id), self.location_id, tag)

        return {
            "success": True,
            "message": f"Added tag '{tag}' to {contact.first_name or 'contact'}"
        }

    async def _handle_send_sms(self, command: CRMCommand) -> Dict[str, Any]:
        """Handle sending SMS."""
        phone = self._get_entity(command, "phone")
        name = self._get_entity(command, "name")

        if not phone and not name:
            return {"success": False, "error": "Who should I text?"}

        # Find contact if name provided
        if name and not phone:
            contacts = await list_contacts(ContactFilter(
                location_id=self.location_id,
                search=name
            ))
            if contacts:
                phone = contacts[0].phone

        if not phone:
            return {"success": False, "error": "Couldn't find phone number"}

        # Extract message (everything after "say" or the whole thing)
        raw = command.raw_input.lower()
        message = None
        for trigger in ["say ", "saying ", "text ", "message "]:
            if trigger in raw:
                idx = raw.index(trigger) + len(trigger)
                message = command.raw_input[idx:].strip().strip('"\'')
                break

        if not message:
            return {
                "success": False,
                "error": "What should the message say?",
                "awaiting": "message_body"
            }

        response = await self.twilio.send_sms(SendSMSRequest(
            to=phone,
            body=message,
            location_id=self.location_id
        ))

        return {
            "success": response.success,
            "message": f"Sent to {phone}" if response.success else response.error
        }

    async def _handle_create_appointment(self, command: CRMCommand) -> Dict[str, Any]:
        """Handle creating appointment."""
        name = self._get_entity(command, "name")
        date = self._get_entity(command, "date_relative") or self._get_entity(command, "date_absolute")
        time = self._get_entity(command, "time")

        if not name:
            return {"success": False, "error": "Who is the appointment with?"}

        # Find contact
        contacts = await list_contacts(ContactFilter(
            location_id=self.location_id,
            search=name
        ))

        if not contacts:
            return {"success": False, "error": f"Couldn't find contact: {name}"}

        contact = contacts[0]

        # Parse datetime
        if date and time:
            dt_str = f"{date} {time}"
        elif date:
            dt_str = f"{date} 09:00"
        else:
            return {"success": False, "error": "When should I schedule it?"}

        # Parse to datetime
        try:
            start_time = datetime.fromisoformat(dt_str)
        except:
            start_time = datetime.now() + timedelta(hours=1)

        appointment_data = AppointmentCreate(
            location_id=self.location_id,
            contact_id=str(contact.id),
            title=f"Call with {contact.first_name or name}",
            start_time=start_time,
            end_time=start_time + timedelta(minutes=30),
            status=AppointmentStatus.SCHEDULED
        )

        appointment = await create_appointment(appointment_data)

        return {
            "success": True,
            "appointment": self._appointment_to_dict(appointment),
            "message": f"Scheduled with {name} on {date} at {time or '9:00 AM'}"
        }

    async def _handle_list_appointments(self, command: CRMCommand) -> Dict[str, Any]:
        """Handle listing appointments."""
        # For now, list all appointments for location
        # TODO: Add date filtering once AppointmentFilter supports it
        from modules.crm_core import get_pool

        pool = await get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT * FROM appointments
                WHERE location_id = $1
                ORDER BY start_time DESC
                LIMIT 20
                """,
                self.location_id
            )

            appointments = [dict(r) for r in rows]

        return {
            "success": True,
            "count": len(appointments),
            "appointments": appointments,
            "message": f"Found {len(appointments)} appointment(s)"
        }

    async def _handle_get_stats(self, command: CRMCommand) -> Dict[str, Any]:
        """Handle stats queries."""
        # Get basic counts
        contacts = await list_contacts(ContactFilter(location_id=self.location_id))

        # Get appointments count
        from modules.crm_core import get_pool
        pool = await get_pool()
        async with pool.acquire() as conn:
            appt_count = await conn.fetchval(
                "SELECT COUNT(*) FROM appointments WHERE location_id = $1",
                self.location_id
            )

        return {
            "success": True,
            "stats": {
                "total_contacts": len(contacts),
                "total_appointments": appt_count,
            }
        }

    def _get_suggestions(self, command: CRMCommand) -> list:
        """Get suggestions for unclear commands."""
        return [
            "Show me leads from today",
            "Find contacts tagged 'hot lead'",
            "Schedule a call with [name] tomorrow at 2pm",
            "Text [name] saying [message]",
            "How many contacts do I have?"
        ]

    def _contact_to_dict(self, contact) -> dict:
        """Convert contact object to dict."""
        if hasattr(contact, 'dict'):
            return contact.dict()
        elif hasattr(contact, '__dict__'):
            return {k: str(v) if not isinstance(v, (str, int, float, bool, type(None))) else v
                    for k, v in contact.__dict__.items()}
        return dict(contact)

    def _appointment_to_dict(self, appointment) -> dict:
        """Convert appointment object to dict."""
        if hasattr(appointment, 'dict'):
            return appointment.dict()
        elif hasattr(appointment, '__dict__'):
            return {k: str(v) if not isinstance(v, (str, int, float, bool, type(None))) else v
                    for k, v in appointment.__dict__.items()}
        return dict(appointment)
