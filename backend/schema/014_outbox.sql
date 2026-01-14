-- Transactional Outbox for Guaranteed Delivery
-- Phase 4 P0-2: Never lose an appointment notification

CREATE TABLE IF NOT EXISTS outbox (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- What we're delivering
    object_type VARCHAR(50) NOT NULL,      -- 'appointment', 'notification', 'email'
    object_id UUID NOT NULL,                -- Reference to the entity

    -- Where it's going
    destination VARCHAR(100) NOT NULL,      -- 'sales_api', 'email', 'sms', 'slack'
    destination_config JSONB DEFAULT '{}',  -- Endpoint URL, email address, etc.

    -- The payload
    payload JSONB NOT NULL,

    -- Delivery status
    status VARCHAR(20) DEFAULT 'pending',   -- pending, sending, sent, failed, dead_letter

    -- Retry tracking
    attempt_count INT DEFAULT 0,
    max_attempts INT DEFAULT 5,
    next_attempt_at TIMESTAMPTZ DEFAULT NOW(),

    -- Error tracking
    last_error TEXT,
    last_error_at TIMESTAMPTZ,

    -- Idempotency
    idempotency_key VARCHAR(255),

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    sent_at TIMESTAMPTZ,

    -- Constraints
    CONSTRAINT valid_status CHECK (status IN ('pending', 'sending', 'sent', 'failed', 'dead_letter', 'cancelled'))
);

-- Fast lookup for worker: pending items ready for processing
CREATE INDEX idx_outbox_pending ON outbox(status, next_attempt_at)
    WHERE status IN ('pending', 'failed');

-- Lookup by object
CREATE INDEX idx_outbox_object ON outbox(object_type, object_id);

-- Lookup by idempotency key
CREATE UNIQUE INDEX idx_outbox_idempotency ON outbox(idempotency_key)
    WHERE idempotency_key IS NOT NULL;

-- Dead letter monitoring
CREATE INDEX idx_outbox_dead_letter ON outbox(status) WHERE status = 'dead_letter';

-- Trigger
DROP TRIGGER IF EXISTS update_outbox_updated_at ON outbox;
CREATE TRIGGER update_outbox_updated_at
    BEFORE UPDATE ON outbox
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
