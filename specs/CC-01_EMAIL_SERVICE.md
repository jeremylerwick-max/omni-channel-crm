# CC-01: Email Service Module

## Overview
Build a complete email marketing service using SendGrid/Resend with deliverability features.

## Repository
`/Users/mac/Desktop/omni-channel-crm`

## Files to Create

### Backend Service
```
backend/app/services/email/
├── __init__.py
├── service.py          # Main email service class
├── providers/
│   ├── __init__.py
│   ├── base.py         # Abstract provider interface
│   ├── sendgrid.py     # SendGrid implementation
│   └── resend.py       # Resend implementation
├── templates.py        # Email template rendering
└── deliverability.py   # Bounce/complaint handling
```

### API Routes
```
backend/app/api/routes/email.py
```

### Database Models (add to existing)
```
backend/app/models/email.py
```

## Database Schema

```sql
CREATE TABLE email_domains (
    id UUID PRIMARY KEY,
    account_id UUID REFERENCES accounts(id),
    domain VARCHAR(255) NOT NULL,
    verified BOOLEAN DEFAULT false,
    spf_verified BOOLEAN DEFAULT false,
    dkim_verified BOOLEAN DEFAULT false,
    dmarc_verified BOOLEAN DEFAULT false,
    provider_domain_id VARCHAR(255),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE email_templates (
    id UUID PRIMARY KEY,
    account_id UUID REFERENCES accounts(id),
    name VARCHAR(255) NOT NULL,
    subject VARCHAR(500),
    html_content TEXT,
    text_content TEXT,
    category VARCHAR(100),
    tokens JSONB DEFAULT '[]',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE email_sends (
    id UUID PRIMARY KEY,
    account_id UUID REFERENCES accounts(id),
    message_id UUID REFERENCES messages(id),
    template_id UUID REFERENCES email_templates(id),
    from_email VARCHAR(255),
    to_email VARCHAR(255),
    subject VARCHAR(500),
    provider VARCHAR(50),
    provider_id VARCHAR(255),
    status VARCHAR(20) DEFAULT 'pending',
    opened_at TIMESTAMPTZ,
    clicked_at TIMESTAMPTZ,
    bounced_at TIMESTAMPTZ,
    complained_at TIMESTAMPTZ,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

## API Endpoints

```python
# Email Routes
POST   /api/v1/email/send              # Send single email
POST   /api/v1/email/send-bulk         # Send to multiple contacts
POST   /api/v1/email/send-template     # Send using template
GET    /api/v1/email/templates         # List templates
POST   /api/v1/email/templates         # Create template
GET    /api/v1/email/templates/{id}    # Get template
PUT    /api/v1/email/templates/{id}    # Update template
DELETE /api/v1/email/templates/{id}    # Delete template
POST   /api/v1/email/templates/{id}/preview  # Preview with test data

# Domain management
GET    /api/v1/email/domains           # List verified domains
POST   /api/v1/email/domains           # Add domain
GET    /api/v1/email/domains/{id}/verify  # Check verification status
DELETE /api/v1/email/domains/{id}      # Remove domain

# Stats
GET    /api/v1/email/stats             # Email stats (sent, opened, clicked)
```

## Service Implementation

```python
# backend/app/services/email/service.py

from abc import ABC, abstractmethod
from typing import List, Optional, Dict
from pydantic import BaseModel, EmailStr

class EmailMessage(BaseModel):
    to: List[EmailStr]
    from_email: EmailStr
    from_name: Optional[str] = None
    subject: str
    html_content: Optional[str] = None
    text_content: Optional[str] = None
    reply_to: Optional[EmailStr] = None
    headers: Dict[str, str] = {}
    tags: List[str] = []
    metadata: Dict = {}

class EmailService:
    def __init__(self, provider: str = "sendgrid"):
        self.provider = self._get_provider(provider)
    
    async def send(self, message: EmailMessage) -> dict:
        """Send a single email."""
        # Validate sender domain
        # Check bounce list
        # Send via provider
        # Log to database
        pass
    
    async def send_bulk(self, messages: List[EmailMessage]) -> dict:
        """Send multiple emails (batch)."""
        pass
    
    async def send_template(
        self, 
        template_id: str, 
        to: EmailStr, 
        data: dict
    ) -> dict:
        """Send email using template with personalization."""
        pass
    
    async def verify_domain(self, domain: str) -> dict:
        """Start domain verification process."""
        pass
    
    async def check_domain_status(self, domain: str) -> dict:
        """Check SPF/DKIM/DMARC status."""
        pass
```

## Provider Interface

```python
# backend/app/services/email/providers/base.py

from abc import ABC, abstractmethod

class EmailProvider(ABC):
    @abstractmethod
    async def send(self, message: EmailMessage) -> dict:
        pass
    
    @abstractmethod
    async def send_batch(self, messages: List[EmailMessage]) -> dict:
        pass
    
    @abstractmethod
    async def add_domain(self, domain: str) -> dict:
        pass
    
    @abstractmethod
    async def verify_domain(self, domain: str) -> dict:
        pass
    
    @abstractmethod
    async def handle_webhook(self, payload: dict) -> None:
        pass
```

## SendGrid Implementation

```python
# backend/app/services/email/providers/sendgrid.py

import sendgrid
from sendgrid.helpers.mail import Mail, Email, To, Content

class SendGridProvider(EmailProvider):
    def __init__(self, api_key: str):
        self.client = sendgrid.SendGridAPIClient(api_key=api_key)
    
    async def send(self, message: EmailMessage) -> dict:
        mail = Mail(
            from_email=Email(message.from_email, message.from_name),
            to_emails=[To(email) for email in message.to],
            subject=message.subject,
            html_content=Content("text/html", message.html_content)
        )
        response = self.client.send(mail)
        return {
            "status_code": response.status_code,
            "message_id": response.headers.get("X-Message-Id")
        }
```

## Webhook Handler (add to webhooks.py)

```python
@router.post("/sendgrid/events")
async def sendgrid_events(request: Request, db: AsyncSession = Depends(get_db)):
    """
    Handle SendGrid events:
    - delivered
    - open
    - click
    - bounce
    - spamreport
    - unsubscribe
    """
    events = await request.json()
    for event in events:
        event_type = event.get("event")
        email = event.get("email")
        message_id = event.get("sg_message_id")
        
        if event_type == "bounce":
            # Mark contact as bounced
            # Update email_sends record
            pass
        elif event_type == "spamreport":
            # Add to suppression list
            # Unsubscribe contact from email
            pass
        # ... handle other events
    
    return {"received": True}
```

## Template Personalization

Support tokens like:
- `{{first_name}}`
- `{{last_name}}`
- `{{company}}`
- `{{custom.field_name}}`
- `{{unsubscribe_link}}`

```python
def render_template(template: str, contact: Contact) -> str:
    """Replace tokens with contact data."""
    rendered = template
    rendered = rendered.replace("{{first_name}}", contact.first_name or "")
    rendered = rendered.replace("{{last_name}}", contact.last_name or "")
    # ... etc
    return rendered
```

## Compliance Features

1. **Unsubscribe Link** - Auto-inject in every email
2. **Physical Address** - Required by CAN-SPAM
3. **Bounce Handling** - Auto-unsubscribe hard bounces
4. **Complaint Handling** - Auto-unsubscribe spam reports
5. **Suppression List** - Global do-not-email list

## Testing

```python
# backend/tests/test_email.py

async def test_send_email():
    service = EmailService(provider="sendgrid")
    result = await service.send(EmailMessage(
        to=["test@example.com"],
        from_email="hello@ziloss.com",
        subject="Test Email",
        html_content="<h1>Hello!</h1>"
    ))
    assert result["status_code"] == 202

async def test_template_rendering():
    template = "Hello {{first_name}}!"
    contact = Contact(first_name="John")
    result = render_template(template, contact)
    assert result == "Hello John!"
```

## Environment Variables

```
SENDGRID_API_KEY=SG.xxxxx
SENDGRID_FROM_EMAIL=hello@yourdomain.com
RESEND_API_KEY=re_xxxxx
EMAIL_PROVIDER=sendgrid
```

## Success Criteria

- [ ] Send single emails via SendGrid
- [ ] Send bulk emails (up to 1000)
- [ ] Template creation and rendering
- [ ] Domain verification flow
- [ ] Webhook handling for events
- [ ] Bounce/complaint auto-handling
- [ ] Unsubscribe link injection
- [ ] API documentation
- [ ] 10+ unit tests passing
