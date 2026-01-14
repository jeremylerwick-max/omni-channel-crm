-- CRM Core Schema - ALTER Migration
-- Add missing columns to existing tables

-- =============================================================================
-- ALTER LOCATIONS TABLE
-- =============================================================================
DO $$
BEGIN
    -- Add slug column
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name='locations' AND column_name='slug') THEN
        ALTER TABLE locations ADD COLUMN slug VARCHAR(100);
    END IF;

    -- Add phone column
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name='locations' AND column_name='phone') THEN
        ALTER TABLE locations ADD COLUMN phone VARCHAR(20);
    END IF;

    -- Add email column
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name='locations' AND column_name='email') THEN
        ALTER TABLE locations ADD COLUMN email VARCHAR(255);
    END IF;

    -- Add address1 column
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name='locations' AND column_name='address1') THEN
        ALTER TABLE locations ADD COLUMN address1 VARCHAR(255);
    END IF;

    -- Add city column
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name='locations' AND column_name='city') THEN
        ALTER TABLE locations ADD COLUMN city VARCHAR(100);
    END IF;

    -- Add state column
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name='locations' AND column_name='state') THEN
        ALTER TABLE locations ADD COLUMN state VARCHAR(50);
    END IF;

    -- Add postal_code column
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name='locations' AND column_name='postal_code') THEN
        ALTER TABLE locations ADD COLUMN postal_code VARCHAR(20);
    END IF;

    -- Add country column
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name='locations' AND column_name='country') THEN
        ALTER TABLE locations ADD COLUMN country VARCHAR(50) DEFAULT 'US';
    END IF;

    -- Add business_hours column
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name='locations' AND column_name='business_hours') THEN
        ALTER TABLE locations ADD COLUMN business_hours JSONB DEFAULT '{}';
    END IF;
END $$;

-- Update existing locations with slugs if they don't have them
UPDATE locations SET slug = LOWER(REPLACE(name, ' ', '-'))
WHERE slug IS NULL;

-- Now make slug NOT NULL and UNIQUE
ALTER TABLE locations ALTER COLUMN slug SET NOT NULL;
CREATE UNIQUE INDEX IF NOT EXISTS idx_locations_slug_unique ON locations(slug);

-- =============================================================================
-- ALTER CONTACTS TABLE
-- =============================================================================
DO $$
BEGIN
    -- Add company_name column
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name='contacts' AND column_name='company_name') THEN
        ALTER TABLE contacts ADD COLUMN company_name VARCHAR(255);
    END IF;

    -- Add website column
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name='contacts' AND column_name='website') THEN
        ALTER TABLE contacts ADD COLUMN website VARCHAR(255);
    END IF;

    -- Add medium column
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name='contacts' AND column_name='medium') THEN
        ALTER TABLE contacts ADD COLUMN medium VARCHAR(100);
    END IF;

    -- Rename contact_type to type if it exists
    IF EXISTS (SELECT 1 FROM information_schema.columns
               WHERE table_name='contacts' AND column_name='contact_type') THEN
        ALTER TABLE contacts RENAME COLUMN contact_type TO type;
    END IF;

    -- Add type column if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name='contacts' AND column_name='type') THEN
        ALTER TABLE contacts ADD COLUMN type VARCHAR(20) DEFAULT 'lead';
    END IF;
END $$;

-- Update index name if needed
DROP INDEX IF EXISTS idx_contacts_type;
CREATE INDEX IF NOT EXISTS idx_contacts_type ON contacts(type);
CREATE INDEX IF NOT EXISTS idx_contacts_assigned_to ON contacts(assigned_to);

-- =============================================================================
-- ALTER MESSAGES TABLE
-- =============================================================================
DO $$
BEGIN
    -- Add contact_id column
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name='messages' AND column_name='contact_id') THEN
        ALTER TABLE messages ADD COLUMN contact_id UUID;

        -- Populate contact_id from conversation
        UPDATE messages m
        SET contact_id = c.contact_id
        FROM conversations c
        WHERE m.conversation_id = c.id;

        -- Make it NOT NULL after populating
        ALTER TABLE messages ALTER COLUMN contact_id SET NOT NULL;

        -- Add foreign key constraint
        ALTER TABLE messages ADD CONSTRAINT fk_messages_contact
            FOREIGN KEY (contact_id) REFERENCES contacts(id) ON DELETE CASCADE;
    END IF;

    -- Add updated_at column
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name='messages' AND column_name='updated_at') THEN
        ALTER TABLE messages ADD COLUMN updated_at TIMESTAMPTZ DEFAULT NOW();
    END IF;

    -- Add status column if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name='messages' AND column_name='status') THEN
        ALTER TABLE messages ADD COLUMN status VARCHAR(20) DEFAULT 'sent';
    END IF;

    -- Add error_message column if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name='messages' AND column_name='error_message') THEN
        ALTER TABLE messages ADD COLUMN error_message TEXT;
    END IF;
END $$;

-- Create indexes for messages
CREATE INDEX IF NOT EXISTS idx_messages_contact ON messages(contact_id);
CREATE INDEX IF NOT EXISTS idx_messages_status ON messages(status);
CREATE INDEX IF NOT EXISTS idx_messages_ai_generated ON messages(ai_generated);

-- Add updated_at trigger for messages
DROP TRIGGER IF EXISTS update_messages_updated_at ON messages;
CREATE TRIGGER update_messages_updated_at BEFORE UPDATE ON messages
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- ALTER APPOINTMENTS TABLE
-- =============================================================================
DO $$
BEGIN
    -- Add description column
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name='appointments' AND column_name='description') THEN
        ALTER TABLE appointments ADD COLUMN description TEXT;
    END IF;

    -- Add location column
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name='appointments' AND column_name='location') THEN
        ALTER TABLE appointments ADD COLUMN location TEXT;
    END IF;

    -- Add assigned_to column
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name='appointments' AND column_name='assigned_to') THEN
        ALTER TABLE appointments ADD COLUMN assigned_to UUID;
    END IF;

    -- Make title NOT NULL if it isn't already
    IF EXISTS (SELECT 1 FROM information_schema.columns
               WHERE table_name='appointments' AND column_name='title' AND is_nullable='YES') THEN
        -- Set default for existing NULL values
        UPDATE appointments SET title = 'Appointment' WHERE title IS NULL;
        ALTER TABLE appointments ALTER COLUMN title SET NOT NULL;
    END IF;
END $$;

-- Create indexes for appointments
CREATE INDEX IF NOT EXISTS idx_appointments_assigned_to ON appointments(assigned_to);
CREATE INDEX IF NOT EXISTS idx_appointments_end ON appointments(end_time);
CREATE INDEX IF NOT EXISTS idx_appointments_calendar_id ON appointments(calendar_id);
CREATE INDEX IF NOT EXISTS idx_appointments_external_id ON appointments(external_id);

-- Rename idx_appointments_location to idx_appointments_location_id if it exists
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_appointments_location') THEN
        ALTER INDEX idx_appointments_location RENAME TO idx_appointments_location_id;
    END IF;
END $$;

-- Success message
DO $$
BEGIN
    RAISE NOTICE 'CRM Core Schema ALTER migration completed successfully!';
END $$;
