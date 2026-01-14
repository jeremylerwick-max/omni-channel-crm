# CC-02: Voice/Call Module
## Claude Code Task Specification

**Module:** Twilio Voice Integration
**Priority:** P1 (MVP Important)
**Estimated Time:** 2-3 days
**Dependencies:** Existing Twilio SMS module

---

## Objective

Add voice calling capabilities using Twilio Voice API - outbound calls, inbound handling, voicemail drops, and call tracking.

---

## Technical Requirements

### 1. Directory Structure
```
backend/modules/voice/
├── __init__.py
├── service.py           # Main voice service
├── twiml_builder.py     # TwiML response builder
├── call_handler.py      # Call flow logic
├── voicemail.py         # Voicemail drop feature
├── recordings.py        # Call recording management
├── transcription.py     # Speech-to-text
├── webhooks.py          # Twilio voice webhooks
└── tests/
    ├── test_outbound.py
    ├── test_inbound.py
    └── test_voicemail.py
```

### 2. Database Schema
```sql
-- backend/schema/021_voice_calls.sql

CREATE TABLE voice_calls (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    location_id UUID NOT NULL,
    contact_id UUID REFERENCES contacts(id),
    twilio_call_sid VARCHAR(50) UNIQUE,
    direction VARCHAR(10) NOT NULL,  -- 'inbound', 'outbound'
    from_number VARCHAR(20) NOT NULL,
    to_number VARCHAR(20) NOT NULL,
    status VARCHAR(30),  -- queued, ringing, in-progress, completed, busy, failed, no-answer, canceled
    duration_seconds INT,
    recording_url TEXT,
    recording_sid VARCHAR(50),
    transcription TEXT,
    voicemail_dropped BOOLEAN DEFAULT FALSE,
    answered_by VARCHAR(20),  -- human, machine, unknown
    disposition VARCHAR(50),  -- Outcome set by user
    notes TEXT,
    cost DECIMAL(10,4),
    started_at TIMESTAMPTZ,
    answered_at TIMESTAMPTZ,
    ended_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE voicemail_drops (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    location_id UUID NOT NULL,
    name VARCHAR(255) NOT NULL,
    audio_url TEXT NOT NULL,
    duration_seconds INT,
    twilio_recording_sid VARCHAR(50),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE call_scripts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    location_id UUID NOT NULL,
    name VARCHAR(255) NOT NULL,
    script_text TEXT NOT NULL,
    twiml_template TEXT,  -- Pre-built TwiML
    variables JSONB DEFAULT '[]',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_voice_calls_contact ON voice_calls(contact_id);
CREATE INDEX idx_voice_calls_status ON voice_calls(status);
CREATE INDEX idx_voice_calls_created ON voice_calls(created_at DESC);
```

### 3. Core Service
```python
# backend/modules/voice/service.py

from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse

class VoiceService:
    async def initiate_call(
        self,
        to_number: str,
        from_number: str,
        contact_id: Optional[str] = None,
        script_id: Optional[str] = None,
        voicemail_drop_id: Optional[str] = None,
        record: bool = True,
        machine_detection: bool = True
    ) -> dict:
        """
        Initiate outbound call with optional:
        - Script playback
        - Voicemail drop on machine answer
        - Recording
        - AMD (Answering Machine Detection)
        """
        pass
    
    async def handle_call_status(self, call_sid: str, status: str, **data):
        """Process Twilio status callback"""
        pass
    
    async def get_recording(self, recording_sid: str) -> bytes:
        """Download call recording"""
        pass
    
    async def transcribe_recording(self, recording_url: str) -> str:
        """Transcribe using Twilio or Whisper"""
        pass
```

### 4. API Endpoints
```
POST   /api/voice/calls                   # Initiate outbound call
GET    /api/voice/calls                   # List calls
GET    /api/voice/calls/{id}              # Get call details
POST   /api/voice/calls/{id}/disposition  # Set call outcome
GET    /api/voice/calls/{id}/recording    # Get recording audio
POST   /api/voice/voicemail-drops         # Upload voicemail drop
GET    /api/voice/voicemail-drops         # List voicemail drops
DELETE /api/voice/voicemail-drops/{id}    # Delete voicemail drop
POST   /api/voice/scripts                 # Create call script
GET    /api/voice/scripts                 # List scripts
PUT    /api/voice/scripts/{id}            # Update script
POST   /api/webhooks/voice/status         # Twilio status callback
POST   /api/webhooks/voice/incoming       # Handle inbound calls
POST   /api/webhooks/voice/recording      # Recording complete
POST   /api/webhooks/voice/transcription  # Transcription complete
```

### 5. TwiML Builder
```python
# backend/modules/voice/twiml_builder.py

def build_outbound_twiml(
    message: Optional[str] = None,
    audio_url: Optional[str] = None,
    gather_input: bool = False,
    action_url: Optional[str] = None
) -> str:
    """Build TwiML response for outbound calls"""
    response = VoiceResponse()
    
    if message:
        response.say(message, voice='alice')
    if audio_url:
        response.play(audio_url)
    if gather_input:
        gather = response.gather(
            num_digits=1,
            action=action_url,
            method='POST'
        )
        gather.say("Press 1 to speak with a representative.")
    
    return str(response)

def build_voicemail_drop_twiml(audio_url: str) -> str:
    """TwiML for voicemail drop (wait for beep, play message)"""
    response = VoiceResponse()
    response.pause(length=2)  # Wait for beep
    response.play(audio_url)
    response.hangup()
    return str(response)
```

### 6. Answering Machine Detection
```python
# Use Twilio's AMD feature
call = client.calls.create(
    to=to_number,
    from_=from_number,
    url=webhook_url,
    machine_detection='DetectMessageEnd',  # Wait for beep
    machine_detection_timeout=30,
    async_amd=True,
    async_amd_status_callback=amd_callback_url
)

# Handle AMD callback
async def handle_amd_result(call_sid: str, answered_by: str):
    if answered_by == 'machine_end_beep':
        # Drop voicemail
        await drop_voicemail(call_sid, voicemail_audio_url)
    elif answered_by == 'human':
        # Continue with script or connect to rep
        pass
```

---

## Acceptance Criteria

1. ✅ Initiate outbound call via API
2. ✅ Handle inbound calls with routing
3. ✅ Voicemail drop on machine answer
4. ✅ Call recording with storage
5. ✅ Transcription (Twilio or Whisper)
6. ✅ AMD (answering machine detection)
7. ✅ Call scripts with TwiML
8. ✅ Status tracking (all Twilio states)
9. ✅ Cost tracking per call
10. ✅ Webhook handlers for all events
11. ✅ 85%+ test coverage

---

## Environment Variables
```
TWILIO_ACCOUNT_SID=ACxxx          # Already set
TWILIO_AUTH_TOKEN=xxx             # Already set
TWILIO_VOICE_NUMBER=+18012129267  # Already set
VOICE_WEBHOOK_BASE_URL=https://yourdomain.com/api/webhooks/voice
VOICE_RECORDING_BUCKET=s3://recordings  # Optional S3 storage
```

---

## Integration Points

- **Workflow Engine:** Trigger on call complete/answered/voicemail
- **Contacts:** Log call in activity timeline
- **Compliance:** Check DND and calling hours
- **Wallet:** Deduct credits ($0.021/minute)

---

## Twilio Pricing Reference

| Resource | Cost |
|----------|------|
| Outbound call (per min) | $0.014 |
| Inbound call (per min) | $0.0085 |
| Recording storage (per min) | $0.0025 |
| Transcription (per min) | $0.05 |
| AMD | $0.0075/call |
