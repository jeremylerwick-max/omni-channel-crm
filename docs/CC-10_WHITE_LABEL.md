# CC-10: White-Label Engine
## Claude Code Task Specification

**Module:** Agency White-Label SaaS Mode
**Priority:** P2 (V1.0)
**Estimated Time:** 3-4 days
**Dependencies:** CC-09 (Billing)

---

## Objective

Enable agencies to resell the platform under their own brand with custom domains, logos, and pricing.

---

## Directory Structure
```
backend/modules/white_label/
├── __init__.py
├── agency.py            # Agency management
├── sub_accounts.py      # Sub-account CRUD
├── branding.py          # Brand customization
├── domains.py           # Custom domain handling
├── pricing.py           # Agency pricing override
└── tests/
```

---

## Database Schema
```sql
-- backend/schema/025_white_label.sql

CREATE TABLE agencies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_account_id UUID NOT NULL,
    name VARCHAR(255) NOT NULL,
    custom_domain VARCHAR(255),
    domain_verified BOOLEAN DEFAULT FALSE,
    branding JSONB DEFAULT '{}',
    pricing_config JSONB DEFAULT '{}',
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE sub_accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agency_id UUID REFERENCES agencies(id),
    name VARCHAR(255) NOT NULL,
    status VARCHAR(20) DEFAULT 'active',
    twilio_subaccount_sid VARCHAR(50),
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## Branding Schema
```json
{
  "app_name": "ClientCRM Pro",
  "logo_light_url": "https://...",
  "logo_dark_url": "https://...",
  "favicon_url": "https://...",
  "primary_color": "#3B82F6",
  "secondary_color": "#10B981",
  "support_email": "support@agency.com",
  "custom_css": ""
}
```

---

## API Endpoints
```
POST   /api/agency/create                 # Create agency
GET    /api/agency                        # Get agency settings
PUT    /api/agency/branding               # Update branding
POST   /api/agency/domain                 # Add custom domain
POST   /api/agency/domain/verify          # Verify domain DNS
GET    /api/agency/sub-accounts           # List sub-accounts
POST   /api/agency/sub-accounts           # Create sub-account
GET    /api/agency/sub-accounts/{id}      # Get sub-account
DELETE /api/agency/sub-accounts/{id}      # Delete sub-account
POST   /api/agency/impersonate/{id}       # Switch to sub-account
```

---

## Custom Domain Flow

1. Agency adds domain: `app.agencydomain.com`
2. System returns DNS instructions (CNAME to our edge)
3. Agency configures DNS
4. Agency clicks "Verify"
5. System checks DNS, provisions SSL
6. Domain goes live

---

## Acceptance Criteria

1. ✅ Create agency from existing account
2. ✅ Create unlimited sub-accounts
3. ✅ Custom branding per agency
4. ✅ Custom domain with auto-SSL
5. ✅ Agency can impersonate sub-accounts
6. ✅ Sub-accounts are fully isolated
7. ✅ Agency pricing override
8. ✅ 80%+ test coverage
