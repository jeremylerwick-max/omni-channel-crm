"""
Phase 4 P0-1: Twilio Phone Number Routing Tests
"""

import pytest
from modules.crm_core import (
    normalize_phone_e164,
    get_location_id_from_twilio_number,
    register_twilio_number,
)


class TestPhoneNormalization:
    """Test phone number normalization to E.164 format."""

    def test_ten_digit(self):
        """Test 10-digit US phone number."""
        assert normalize_phone_e164("5551234567") == "+15551234567"

    def test_formatted(self):
        """Test formatted phone number with parentheses and dashes."""
        assert normalize_phone_e164("(555) 123-4567") == "+15551234567"

    def test_dotted(self):
        """Test phone number with dots."""
        assert normalize_phone_e164("555.123.4567") == "+15551234567"

    def test_with_country_code(self):
        """Test phone number with country code and spaces."""
        assert normalize_phone_e164("+1 555 123 4567") == "+15551234567"

    def test_eleven_digit(self):
        """Test 11-digit number starting with 1."""
        assert normalize_phone_e164("15551234567") == "+15551234567"

    def test_with_plus_prefix(self):
        """Test number already with + prefix."""
        assert normalize_phone_e164("+15551234567") == "+15551234567"


class TestTwilioRouting:
    """Test Twilio phone number to location routing."""

    @pytest.mark.asyncio
    async def test_register_and_lookup(self):
        """Test registering a number and looking it up."""
        # Use default location that exists
        default_location = "00000000-0000-0000-0000-000000000001"

        # Register a number
        await register_twilio_number(
            phone_number="+15559876543",
            location_id=default_location,
            friendly_name="Test Number"
        )

        # Look it up
        location = await get_location_id_from_twilio_number("+15559876543")
        assert location == default_location

    @pytest.mark.asyncio
    async def test_unknown_number_returns_none(self):
        """Test that unknown numbers return None."""
        location = await get_location_id_from_twilio_number("+19999999999")
        assert location is None

    @pytest.mark.asyncio
    async def test_different_formats_same_result(self):
        """Test that different phone formats resolve to same location."""
        default_location = "00000000-0000-0000-0000-000000000001"
        await register_twilio_number("+15551112222", default_location)

        # All these should find the same location
        assert await get_location_id_from_twilio_number("5551112222") == default_location
        assert await get_location_id_from_twilio_number("(555) 111-2222") == default_location
        assert await get_location_id_from_twilio_number("+1-555-111-2222") == default_location

    @pytest.mark.asyncio
    async def test_register_updates_existing(self):
        """Test that re-registering a number updates it."""
        default_location = "00000000-0000-0000-0000-000000000001"

        # Register once
        await register_twilio_number(
            phone_number="+15553334444",
            location_id=default_location,
            friendly_name="First Name"
        )

        # Register again with same location but different name
        await register_twilio_number(
            phone_number="+15553334444",
            location_id=default_location,
            friendly_name="Second Name"
        )

        # Should still map to same location
        location = await get_location_id_from_twilio_number("+15553334444")
        assert location == default_location
