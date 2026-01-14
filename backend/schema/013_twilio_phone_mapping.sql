-- Twilio Phone Number to Location Mapping
-- Phase 4 P0-1: Multi-tenant routing

CREATE TABLE IF NOT EXISTS twilio_phone_numbers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- The Twilio number in E.164 format (+15551234567)
    phone_number VARCHAR(20) NOT NULL,

    -- Which location/tenant owns this number
    location_id UUID NOT NULL REFERENCES locations(id) ON DELETE CASCADE,

    -- Twilio metadata
    twilio_sid VARCHAR(50),           -- Twilio Phone Number SID (PN...)
    friendly_name VARCHAR(100),        -- Human readable name

    -- Capabilities
    sms_enabled BOOLEAN DEFAULT TRUE,
    voice_enabled BOOLEAN DEFAULT FALSE,
    mms_enabled BOOLEAN DEFAULT FALSE,

    -- Status
    is_active BOOLEAN DEFAULT TRUE,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Unique constraint: one phone can only belong to one location
CREATE UNIQUE INDEX idx_twilio_phones_number_unique
    ON twilio_phone_numbers(phone_number) WHERE is_active = TRUE;

-- Fast lookup by phone number
CREATE INDEX idx_twilio_phones_number ON twilio_phone_numbers(phone_number);

-- List all numbers for a location
CREATE INDEX idx_twilio_phones_location ON twilio_phone_numbers(location_id);

-- Trigger for updated_at
DROP TRIGGER IF EXISTS update_twilio_phone_numbers_updated_at ON twilio_phone_numbers;
CREATE TRIGGER update_twilio_phone_numbers_updated_at
    BEFORE UPDATE ON twilio_phone_numbers
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert test number for default location
INSERT INTO twilio_phone_numbers (phone_number, location_id, twilio_sid, friendly_name)
VALUES ('+18012129267', '00000000-0000-0000-0000-000000000001', 'PN_test_default', 'Default Test Number')
ON CONFLICT DO NOTHING;
