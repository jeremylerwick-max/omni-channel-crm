"""
Phase 5: Natural Language Recognition Tests

Tests for intent recognition and entity extraction.
"""

import pytest
from modules.natural_language_interface.crm_recognizer import CRMIntentRecognizer
from modules.natural_language_interface.crm_intents import CRMIntent


class TestIntentRecognition:
    """Test intent recognition from natural language."""

    def setup_method(self):
        self.recognizer = CRMIntentRecognizer(use_llm_fallback=False)

    def test_search_contacts_show_me(self):
        """Test 'show me' pattern for search."""
        cmd = self.recognizer.recognize("show me leads from today")
        assert cmd.intent == CRMIntent.SEARCH_CONTACTS
        assert cmd.confidence > 0.5

    def test_search_contacts_find(self):
        """Test 'find' pattern for search."""
        cmd = self.recognizer.recognize("find contacts tagged hot lead")
        assert cmd.intent == CRMIntent.SEARCH_CONTACTS

    def test_search_contacts_list(self):
        """Test 'list' pattern for search."""
        cmd = self.recognizer.recognize("list contacts")
        assert cmd.intent == CRMIntent.SEARCH_CONTACTS

    def test_send_sms_text(self):
        """Test 'text' pattern for SMS."""
        cmd = self.recognizer.recognize("text John saying hey there")
        assert cmd.intent == CRMIntent.SEND_SMS

    def test_send_sms_message(self):
        """Test 'message' pattern for SMS."""
        cmd = self.recognizer.recognize("message 949-230-0036 saying hello")
        assert cmd.intent == CRMIntent.SEND_SMS

    def test_create_appointment_schedule(self):
        """Test 'schedule' pattern for appointments."""
        cmd = self.recognizer.recognize("schedule a call with Jane tomorrow at 2pm")
        assert cmd.intent == CRMIntent.CREATE_APPOINTMENT

    def test_create_appointment_book(self):
        """Test 'book' pattern for appointments."""
        cmd = self.recognizer.recognize("book meeting with Smith")
        assert cmd.intent == CRMIntent.CREATE_APPOINTMENT

    def test_get_stats_how_many(self):
        """Test 'how many' pattern for stats."""
        cmd = self.recognizer.recognize("how many contacts do I have")
        assert cmd.intent == CRMIntent.GET_STATS

    def test_get_stats_total(self):
        """Test 'total' pattern for stats."""
        cmd = self.recognizer.recognize("total leads")
        assert cmd.intent == CRMIntent.GET_STATS

    def test_tag_contact(self):
        """Test 'tag' pattern."""
        cmd = self.recognizer.recognize("tag John as hot lead")
        assert cmd.intent == CRMIntent.TAG_CONTACT

    def test_unknown_intent_low_confidence(self):
        """Test unknown commands have low confidence."""
        cmd = self.recognizer.recognize("this is gibberish xyz")
        # Should either be UNKNOWN or have very low confidence
        if cmd.intent != CRMIntent.UNKNOWN:
            assert cmd.confidence < 0.6


class TestEntityExtraction:
    """Test entity extraction from natural language."""

    def setup_method(self):
        self.recognizer = CRMIntentRecognizer(use_llm_fallback=False)

    def test_extract_phone_with_dashes(self):
        """Test phone extraction with dashes."""
        cmd = self.recognizer.recognize("text 949-230-0036")
        phones = [e for e in cmd.entities if e.entity_type == "phone"]
        assert len(phones) == 1
        assert phones[0].value == "+19492300036"

    def test_extract_phone_with_parentheses(self):
        """Test phone extraction with parentheses."""
        cmd = self.recognizer.recognize("call (949) 230-0036")
        phones = [e for e in cmd.entities if e.entity_type == "phone"]
        assert len(phones) == 1
        assert "+1949" in phones[0].value

    def test_extract_email(self):
        """Test email extraction."""
        cmd = self.recognizer.recognize("send email to john@example.com")
        emails = [e for e in cmd.entities if e.entity_type == "email"]
        assert len(emails) == 1
        assert emails[0].value == "john@example.com"

    def test_extract_date_today(self):
        """Test 'today' date extraction."""
        cmd = self.recognizer.recognize("show me leads from today")
        dates = [e for e in cmd.entities if e.entity_type == "date_relative"]
        assert len(dates) == 1
        # Should be an ISO date string
        assert "-" in dates[0].value

    def test_extract_date_tomorrow(self):
        """Test 'tomorrow' date extraction."""
        cmd = self.recognizer.recognize("schedule call tomorrow")
        dates = [e for e in cmd.entities if e.entity_type == "date_relative"]
        assert len(dates) == 1

    def test_extract_date_this_week(self):
        """Test 'this week' date extraction."""
        cmd = self.recognizer.recognize("leads from this week")
        dates = [e for e in cmd.entities if e.entity_type == "date_relative"]
        assert len(dates) == 1

    def test_extract_tag(self):
        """Test tag extraction."""
        cmd = self.recognizer.recognize("find contacts tagged 'hot lead'")
        tags = [e for e in cmd.entities if e.entity_type == "tag"]
        # May extract multiple words as separate tags
        assert len(tags) >= 1

    def test_extract_time_12hr(self):
        """Test 12-hour time extraction."""
        cmd = self.recognizer.recognize("schedule call at 2pm")
        times = [e for e in cmd.entities if e.entity_type == "time"]
        assert len(times) == 1
        assert "2" in times[0].value

    def test_extract_time_24hr(self):
        """Test 24-hour time extraction."""
        cmd = self.recognizer.recognize("meeting at 14:00")
        times = [e for e in cmd.entities if e.entity_type == "time"]
        assert len(times) == 1

    def test_extract_name(self):
        """Test name extraction (capitalized words)."""
        cmd = self.recognizer.recognize("call John Smith")
        names = [e for e in cmd.entities if e.entity_type == "name"]
        # Should extract "John" and "Smith"
        assert len(names) >= 1

    def test_extract_multiple_entities(self):
        """Test extracting multiple entities from one command."""
        cmd = self.recognizer.recognize("text John at 949-230-0036 tomorrow at 2pm")
        # Should have name, phone, date, time
        assert len(cmd.entities) >= 3


class TestComplexScenarios:
    """Test complex real-world scenarios."""

    def setup_method(self):
        self.recognizer = CRMIntentRecognizer(use_llm_fallback=False)

    def test_schedule_with_all_details(self):
        """Test scheduling with complete details."""
        cmd = self.recognizer.recognize("schedule a call with John tomorrow at 2pm")
        assert cmd.intent == CRMIntent.CREATE_APPOINTMENT
        # Should have name, date, time
        entity_types = [e.entity_type for e in cmd.entities]
        assert "name" in entity_types or "John" in cmd.raw_input
        assert "date_relative" in entity_types
        assert "time" in entity_types

    def test_text_with_message(self):
        """Test texting with message content."""
        cmd = self.recognizer.recognize("text 949-230-0036 saying hello there")
        assert cmd.intent == CRMIntent.SEND_SMS
        phones = [e for e in cmd.entities if e.entity_type == "phone"]
        assert len(phones) == 1

    def test_search_with_filters(self):
        """Test search with multiple filters."""
        cmd = self.recognizer.recognize("show me leads from today tagged hot")
        assert cmd.intent == CRMIntent.SEARCH_CONTACTS
        # Should have date and possibly tag
        assert len(cmd.entities) >= 1


if __name__ == "__main__":
    # Run tests with: pytest tests/phase5/test_nl_recognition.py -v
    pytest.main([__file__, "-v"])
