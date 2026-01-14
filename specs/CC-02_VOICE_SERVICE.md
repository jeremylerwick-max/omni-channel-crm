# CC-02: Voice/Call Service

## Overview
Twilio Voice integration for outbound calls, voicemail drops, and call tracking.

## Priority
P1 - Completes omni-channel

## Key Features
- Outbound call initiation
- Voicemail drop (pre-recorded messages)
- Call status tracking (answered, voicemail, no-answer, busy)
- Call recording (optional)
- Call transcription (via Twilio)
- Click-to-call from CRM

## Files to Create
```
backend/app/services/voice/
├── __init__.py
├── service.py        # Main voice service
├── voicemail.py      # Voicemail drop logic
└── transcription.py  # Call transcription
```

## Database
```sql
CREATE TABLE calls (
    id UUID PRIMARY KEY,
    account_id UUID,
    contact_id UUID,
    direction VARCHAR(10),
    status VARCHAR(20),
    duration_seconds INT,
    recording_url TEXT,
    transcription TEXT,
    twilio_call_sid VARCHAR(50),
    created_at TIMESTAMPTZ
);
```

## API Endpoints
```
POST /api/v1/voice/call          # Initiate call
POST /api/v1/voice/voicemail     # Drop voicemail
GET  /api/v1/voice/calls         # List calls
GET  /api/v1/voice/calls/{id}    # Get call details
```

## Success Criteria
- [ ] Initiate outbound calls
- [ ] Voicemail drop functionality
- [ ] Call status webhooks
- [ ] Call recording storage
- [ ] Call transcription
- [ ] Integration with workflows
