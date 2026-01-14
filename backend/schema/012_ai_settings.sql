-- Migration 012: Add AI settings to locations
-- Adds AI conversation engine configuration to locations table

DO $$
BEGIN
    -- Add ai_enabled column if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'locations' AND column_name = 'ai_enabled'
    ) THEN
        ALTER TABLE locations
        ADD COLUMN ai_enabled BOOLEAN DEFAULT false NOT NULL;
    END IF;

    -- Add ai_model column if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'locations' AND column_name = 'ai_model'
    ) THEN
        ALTER TABLE locations
        ADD COLUMN ai_model TEXT DEFAULT 'claude-3-haiku-20240307';
    END IF;
END $$;

-- Add comment
COMMENT ON COLUMN locations.ai_enabled IS 'Whether AI conversation responses are enabled for this location';
COMMENT ON COLUMN locations.ai_model IS 'Claude model to use for AI responses (e.g., claude-3-haiku-20240307)';
