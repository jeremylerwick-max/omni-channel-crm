# CC-01: Email Service Module
## Claude Code Task Specification

**Module:** Email Marketing Service
**Priority:** P0 (MVP Critical)
**Estimated Time:** 2-3 days
**Dependencies:** None (can start immediately)

---

## Objective

Build a complete email marketing service with SendGrid/Resend integration, supporting transactional and campaign emails with full tracking.

---

## Technical Requirements

### 1. Directory Structure
```
backend/modules/email_service/
├── __init__.py
├── providers/
│   ├── __init__.py
│   ├── base.py          # Abstract provider interface
│   ├── sendgrid.py      # SendGrid implementation
│   ├── resend.py        # Resend implementation
│   └── ses.py           # Amazon SES (future)
├── models.py             # Pydantic models
├── service.py            # Main service logic
├── templates.py          # Template engine
├── tracking.py           # Open/click tracking
├── webhooks.py           # Webhook handlers
└── tests/
    ├── test_sendgrid.py
    ├── test_resend.py
    └── test_templates.py
```

### 2. Database Schema
```sql
-- Add to backend/schema/020_email_service.sql

CREATE TABLE email_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    location_id UUID NOT NULL,
    name VARCHAR(255) NOT NULL,
    subject VARCHAR(500) NOT NULL,
    body_html TEXT NOT NULL,
    body_text TEXT,
    variables JSONB DEFAULT '[]',  -- Available merge fields
    category VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE email_sends (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    location_id UUID NOT NULL,
    contact_id UUID REFERENCES contacts(id),
    template_id UUID REFERENCES email_templates(id),
    provider VARCHAR(50) NOT NULL,  -- 'sendgrid', 'resend', 'ses'
    provider_message_id VARCHAR(255),
    from_email VARCHAR(255) NOT NULL,
    from_name VARCHAR(255),
    to_email VARCHAR(255) NOT NULL,
    subject VARCHAR(500) NOT NULL,
    status VARCHAR(50) DEFAULT 'queued',  -- queued, sent, delivered, opened, clicked, bounced, complained
    opened_at TIMESTAMPTZ,
    clicked_at TIMESTAMPTZ,
    bounced_at TIMESTAMPTZ,
    bounce_type VARCHAR(50),
    error_message TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE email_clicks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email_send_id UUID REFERENCES email_sends(id),
    url TEXT NOT NULL,
    clicked_at TIMESTAMPTZ DEFAULT NOW(),
    user_agent TEXT,
    ip_address INET
);

CREATE TABLE email_domains (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    location_id UUID NOT NULL,
    domain VARCHAR(255) NOT NULL UNIQUE,
    verified BOOLEAN DEFAULT FALSE,
    dkim_record TEXT,
    spf_record TEXT,
    verification_token VARCHAR(255),
    verified_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_email_sends_contact ON email_sends(contact_id);
CREATE INDEX idx_email_sends_status ON email_sends(status);
CREATE INDEX idx_email_sends_created ON email_sends(created_at DESC);
```

### 3. Provider Interface
```python
# backend/modules/email_service/providers/base.py

from abc import ABC, abstractmethod
from typing import List, Optional
from pydantic import BaseModel

class EmailMessage(BaseModel):
    to_email: str
    to_name: Optional[str] = None
    from_email: str
    from_name: Optional[str] = None
    subject: str
    body_html: str
    body_text: Optional[str] = None
    reply_to: Optional[str] = None
    headers: dict = {}
    tracking_id: Optional[str] = None

class SendResult(BaseModel):
    success: bool
    provider_message_id: Optional[str] = None
    error: Optional[str] = None

class EmailProvider(ABC):
    @abstractmethod
    async def send(self, message: EmailMessage) -> SendResult:
        pass
    
    @abstractmethod
    async def send_batch(self, messages: List[EmailMessage]) -> List[SendResult]:
        pass
    
    @abstractmethod
    async def verify_domain(self, domain: str) -> dict:
        pass
    
    @abstractmethod
    async def check_domain_status(self, domain: str) -> dict:
        pass
```

### 4. API Endpoints
```
POST   /api/email/send                    # Send single email
POST   /api/email/send-batch              # Send to multiple recipients
POST   /api/email/templates               # Create template
GET    /api/email/templates               # List templates
GET    /api/email/templates/{id}          # Get template
PUT    /api/email/templates/{id}          # Update template
DELETE /api/email/templates/{id}          # Delete template
POST   /api/email/templates/{id}/preview  # Preview with merge fields
GET    /api/email/sends                   # List sent emails
GET    /api/email/sends/{id}              # Get send details
GET    /api/email/analytics               # Email analytics
POST   /api/email/domains                 # Add domain
GET    /api/email/domains                 # List domains
POST   /api/email/domains/{id}/verify     # Verify domain
POST   /api/webhooks/sendgrid             # SendGrid webhooks
POST   /api/webhooks/resend               # Resend webhooks
```

### 5. Template Engine
```python
# Support Jinja2-style variables
# {{contact.first_name}}, {{contact.email}}, {{unsubscribe_url}}

REQUIRED_VARIABLES = [
    "unsubscribe_url",      # CAN-SPAM compliance
    "physical_address",     # CAN-SPAM compliance
    "company_name"          # Sender identification
]

# Template must include footer with unsubscribe link
COMPLIANCE_FOOTER = """
<div style="margin-top: 20px; padding-top: 20px; border-top: 1px solid #eee; font-size: 12px; color: #666;">
    <p>{{company_name}}<br>{{physical_address}}</p>
    <p><a href="{{unsubscribe_url}}">Unsubscribe</a></p>
</div>
"""
```

### 6. Tracking Implementation
```python
# Open tracking: 1x1 transparent pixel
# GET /api/email/track/open/{tracking_id}

# Click tracking: Redirect through our server
# GET /api/email/track/click/{tracking_id}?url={encoded_url}

# Both update email_sends table and emit events for workflow triggers
```

---

## Acceptance Criteria

1. ✅ Send email via SendGrid API
2. ✅ Send email via Resend API
3. ✅ Template creation with variable substitution
4. ✅ Open tracking (pixel)
5. ✅ Click tracking (redirect)
6. ✅ Webhook handling for bounces/complaints
7. ✅ Auto-unsubscribe on hard bounce
8. ✅ Domain verification flow
9. ✅ CAN-SPAM compliant footer injection
10. ✅ Batch sending (up to 1000/call)
11. ✅ Rate limiting per provider
12. ✅ 90%+ test coverage

---

## Environment Variables
```
SENDGRID_API_KEY=SG.xxx
RESEND_API_KEY=re_xxx
EMAIL_PROVIDER=sendgrid  # or resend
EMAIL_FROM_DEFAULT=noreply@yourdomain.com
EMAIL_TRACKING_DOMAIN=https://track.yourdomain.com
```

---

## Integration Points

- **Workflow Engine:** Emit events on send/open/click/bounce
- **Contacts:** Auto-update email opt-out on unsubscribe
- **Compliance:** Check DND before sending
- **Wallet:** Deduct credits on send ($0.0002/email)

---

## Reference Code

Look at existing patterns in:
- `backend/modules/twilio_sms/` - Similar provider abstraction
- `backend/modules/crm_core/` - Database patterns
