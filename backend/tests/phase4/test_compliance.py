"""
Phase 4 Compliance Tests

Tests for opt-out detection, DND enforcement, and compliance workflows.
"""

import pytest
from modules.compliance.optout import is_optout, is_optin


class TestOptOutDetection:
    """Test deterministic opt-out keyword detection."""

    def test_exact_keyword_stop(self):
        """Test exact 'STOP' keyword (Twilio standard)."""
        assert is_optout("STOP") is True
        assert is_optout("stop") is True
        assert is_optout("Stop") is True

    def test_exact_keywords_variants(self):
        """Test other exact opt-out keywords."""
        assert is_optout("UNSUBSCRIBE") is True
        assert is_optout("cancel") is True
        assert is_optout("quit") is True
        assert is_optout("end") is True
        assert is_optout("optout") is True
        assert is_optout("opt-out") is True

    def test_phrase_please_stop(self):
        """Test 'please stop texting' phrase."""
        assert is_optout("please stop texting me") is True
        assert is_optout("Please stop messaging") is True
        assert is_optout("pls stop") is True

    def test_phrase_remove_me(self):
        """Test 'remove me' phrase."""
        assert is_optout("remove me from your list") is True
        assert is_optout("Remove me") is True
        assert is_optout("take me off") is True
        assert is_optout("take me off your list") is True

    def test_phrase_wrong_number(self):
        """Test 'wrong number' phrase."""
        assert is_optout("wrong number") is True
        assert is_optout("Wrong number, stop texting") is True

    def test_phrase_not_interested(self):
        """Test 'not interested' and variants."""
        assert is_optout("not interested") is True
        assert is_optout("I'm not interested") is True
        assert is_optout("leave me alone") is True

    def test_phrase_do_not_contact(self):
        """Test 'do not contact' and variants."""
        assert is_optout("do not contact me") is True
        assert is_optout("don't text me") is True
        assert is_optout("dont text") is True
        assert is_optout("stop contacting me") is True
        assert is_optout("never contact me again") is True

    def test_negation_dont_stop(self):
        """Test negation: 'don't stop' should NOT be opt-out."""
        assert is_optout("don't stop texting") is False
        assert is_optout("dont stop") is False
        assert is_optout("do not stop") is False
        assert is_optout("please don't remove me") is False

    def test_negation_not_yet(self):
        """Test negation: 'not yet' should NOT be opt-out."""
        assert is_optout("not yet, keep texting") is False

    def test_contextual_stop_not_optout(self):
        """Test contextual use of 'stop' that is NOT opt-out."""
        # These should NOT trigger opt-out (contextual use)
        assert is_optout("Can we stop by your office?") is False
        assert is_optout("The bus will stop at 3pm") is False

        # But these SHOULD trigger (opt-out intent)
        assert is_optout("Stop this") is True
        assert is_optout("stop please") is True
        assert is_optout("stop!!") is True

    def test_empty_or_none(self):
        """Test empty or None messages."""
        assert is_optout("") is False
        assert is_optout(None) is False
        assert is_optout("   ") is False

    def test_case_insensitive(self):
        """Test case insensitivity."""
        assert is_optout("STOP TEXTING ME") is True
        assert is_optout("Stop Texting Me") is True
        assert is_optout("stop texting me") is True


class TestOptInDetection:
    """Test deterministic opt-in keyword detection."""

    def test_exact_keyword_start(self):
        """Test exact 'START' keyword (Twilio standard)."""
        assert is_optin("START") is True
        assert is_optin("start") is True
        assert is_optin("Start") is True

    def test_exact_keywords_variants(self):
        """Test other exact opt-in keywords."""
        assert is_optin("SUBSCRIBE") is True
        assert is_optin("unstop") is True
        assert is_optin("yes") is True
        assert is_optin("resume") is True
        assert is_optin("optin") is True

    def test_phrase_yes_subscribe(self):
        """Test opt-in phrases."""
        assert is_optin("yes subscribe") is True
        assert is_optin("Yes, subscribe me") is True

    def test_not_optin(self):
        """Test messages that are NOT opt-in."""
        assert is_optin("maybe") is False
        assert is_optin("no") is False
        assert is_optin("hello") is False

    def test_case_insensitive(self):
        """Test case insensitivity."""
        assert is_optin("START") is True
        assert is_optin("Start") is True
        assert is_optin("start") is True


class TestDNDEnforcement:
    """Test DND enforcement in SMS sender."""

    @pytest.mark.asyncio
    async def test_dnd_blocks_send(self):
        """Test that DND=true blocks all outbound SMS."""
        # This test would require:
        # 1. Create a contact with DND=true
        # 2. Attempt to send SMS to that contact
        # 3. Verify send is blocked with blocked_reason="dnd"

        # Placeholder for now - full implementation requires DB setup
        # from modules.twilio_sms import TwilioSMSExecutor
        # from modules.twilio_sms.models import SendSMSRequest
        # from modules.crm_core import create_contact, ContactCreate

        # contact = await create_contact(ContactCreate(
        #     location_id="test-location",
        #     phone="+15551234567",
        #     dnd=True
        # ))

        # executor = TwilioSMSExecutor()
        # request = SendSMSRequest(
        #     to="+15551234567",
        #     body="Test message",
        #     location_id="test-location",
        #     contact_id=contact.id
        # )

        # response = await executor.send_sms(request)
        # assert response.success is False
        # assert response.blocked_reason == "dnd"

        pass  # Placeholder


class TestOptOutWorkflow:
    """Test complete opt-out workflow in webhook handler."""

    @pytest.mark.asyncio
    async def test_conversation_closed_on_optout(self):
        """Test that conversation is closed when contact opts out."""
        # Placeholder - requires webhook test setup
        # 1. Send inbound SMS with "STOP"
        # 2. Verify conversation status = "closed"
        # 3. Verify contact.dnd = True
        # 4. Verify "opted_out" tag added
        pass

    @pytest.mark.asyncio
    async def test_pending_outbox_cancelled_on_optout(self):
        """Test that pending outbox items are cancelled on opt-out."""
        # Placeholder - requires outbox setup
        # 1. Create pending outbox items for contact
        # 2. Send opt-out message
        # 3. Verify outbox items are cancelled
        pass

    @pytest.mark.asyncio
    async def test_confirmation_sent_on_optout(self):
        """Test that ONE confirmation SMS is sent on opt-out."""
        # Placeholder
        # 1. Send opt-out message
        # 2. Verify exactly one confirmation sent
        # 3. Verify no further messages sent
        pass

    @pytest.mark.asyncio
    async def test_no_ai_response_after_optout(self):
        """Test that AI does not respond after opt-out detected."""
        # Placeholder
        # 1. Send opt-out message
        # 2. Verify no AI-generated response is sent
        # 3. Only confirmation message sent
        pass


class TestOptInWorkflow:
    """Test opt-in (resubscribe) workflow."""

    @pytest.mark.asyncio
    async def test_optin_clears_dnd(self):
        """Test that opt-in clears DND flag."""
        # Placeholder
        # 1. Create contact with DND=true
        # 2. Send "START" message
        # 3. Verify contact.dnd = False
        # 4. Verify "opted_in" tag added
        pass

    @pytest.mark.asyncio
    async def test_optin_reopens_conversation(self):
        """Test that opt-in reopens closed conversation."""
        # Placeholder
        # 1. Create contact with closed conversation
        # 2. Send "START" message
        # 3. Verify conversation status = "open"
        pass


# Additional tests for edge cases
class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_multiple_keywords_in_message(self):
        """Test message with multiple opt-out keywords."""
        assert is_optout("stop texting me, remove me from your list") is True

    def test_punctuation_and_formatting(self):
        """Test opt-out keywords with punctuation."""
        assert is_optout("STOP!!!") is True
        assert is_optout("stop.") is True
        assert is_optout("stop?") is True

    def test_international_characters(self):
        """Test that non-ASCII characters don't break detection."""
        # These should still detect 'stop'
        assert is_optout("stop 🛑") is True
        assert is_optout("please stop 😭") is True

    def test_very_long_message(self):
        """Test opt-out detection in very long messages."""
        long_msg = "This is a really long message. " * 20 + " Please stop texting me."
        assert is_optout(long_msg) is True


if __name__ == "__main__":
    # Run tests with: pytest tests/phase4/test_compliance.py -v
    pytest.main([__file__, "-v"])
