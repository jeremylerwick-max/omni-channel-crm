# PRD Addendum: Missing Requirements
## Omni-Channel CRM & Automation Platform

**Version:** 1.0  
**Date:** January 13, 2026  
**Author:** Ziloss Technologies  
**Status:** Required for MVP Completion

---

## Overview

This addendum addresses critical gaps identified in the core PRD that are essential for:
1. Monetization and revenue generation
2. Agency adoption and white-label reselling
3. Competitive migration from GoHighLevel/HubSpot
4. US SMS compliance (10DLC)
5. Enterprise privacy requirements

---

## 1. Billing & Wallet System

### 1.1 Subscription Management

**Requirement:** Integrate Stripe for recurring subscription billing.

**Pricing Tiers:**
| Tier | Price | Contacts | Users | Features |
|------|-------|----------|-------|----------|
| Starter | $97/mo | 5,000 | 3 | Core CRM, SMS, Email |
| Professional | $297/mo | 25,000 | 10 | + Workflows, AI Testing |
| Agency | $497/mo | 100,000 | Unlimited | + White-Label, Sub-accounts |
| Enterprise | Custom | Unlimited | Unlimited | + Dedicated Support, SLA |

**Implementation:**
```
POST /api/billing/subscribe
POST /api/billing/upgrade
POST /api/billing/cancel
GET  /api/billing/invoices
GET  /api/billing/usage
```

### 1.2 Usage-Based Rebilling (Wallet System)

**Requirement:** Track and charge for variable usage with markup capability.

**Billable Resources:**
| Resource | Cost (to us) | Default Markup | Charged to User |
|----------|--------------|----------------|-----------------|
| SMS Outbound | $0.0079 | 50% | $0.012 |
| SMS Inbound | $0.0079 | 50% | $0.012 |
| MMS Outbound | $0.02 | 50% | $0.03 |
| Voice (per min) | $0.014 | 50% | $0.021 |
| Email | $0.0001 | 100% | $0.0002 |
| AI Tokens (1K) | $0.003 | 100% | $0.006 |

**Wallet Architecture:**
```sql
CREATE TABLE wallets (
    id UUID PRIMARY KEY,
    account_id UUID REFERENCES accounts(id),
    balance DECIMAL(10,4) DEFAULT 0,
    auto_recharge BOOLEAN DEFAULT true,
    recharge_threshold DECIMAL(10,2) DEFAULT 10.00,
    recharge_amount DECIMAL(10,2) DEFAULT 50.00,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE wallet_transactions (
    id UUID PRIMARY KEY,
    wallet_id UUID REFERENCES wallets(id),
    type VARCHAR(20), -- 'credit', 'debit', 'refund'
    amount DECIMAL(10,4),
    resource_type VARCHAR(50), -- 'sms', 'email', 'voice', 'ai'
    resource_id VARCHAR(255), -- Twilio SID, etc.
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

**API Endpoints:**
```
GET  /api/wallet/balance
POST /api/wallet/add-funds
GET  /api/wallet/transactions
POST /api/wallet/auto-recharge/configure
```

### 1.3 Dunning & Failed Payments

**Requirement:** Handle failed payments gracefully without losing customers.

**Dunning Flow:**
1. Payment fails → Retry in 24 hours
2. Second failure → Email warning, retry in 48 hours
3. Third failure → Pause automations, show banner in app
4. Fourth failure (Day 7) → Downgrade to free tier, retain data
5. Day 30 → Archive account (no deletion)

**Implementation:**
- Stripe webhook handlers for `invoice.payment_failed`
- Account status field: `active`, `past_due`, `paused`, `archived`
- Workflows check account status before executing

---

## 2. White-Label / SaaS Mode

### 2.1 Agency Sub-Accounts

**Requirement:** Agencies can create and manage client sub-accounts.

**Data Model:**
```sql
CREATE TABLE agencies (
    id UUID PRIMARY KEY,
    name VARCHAR(255),
    owner_account_id UUID REFERENCES accounts(id),
    custom_domain VARCHAR(255),
    branding JSONB DEFAULT '{}',
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE sub_accounts (
    id UUID PRIMARY KEY,
    agency_id UUID REFERENCES agencies(id),
    name VARCHAR(255),
    -- Each sub-account is a full tenant
    twilio_subaccount_sid VARCHAR(50),
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

**Features:**
- Agencies create unlimited sub-accounts
- Each sub-account is isolated (contacts, workflows, messages)
- Agency can access any sub-account (impersonation)
- Sub-accounts can have their own users

### 2.2 Custom Branding

**Requirement:** Full white-label capability for agencies.

**Customizable Elements:**
| Element | Scope | Storage |
|---------|-------|---------|
| Logo (light) | Header, emails | S3/Cloudflare |
| Logo (dark) | Dark mode | S3/Cloudflare |
| Favicon | Browser tab | S3/Cloudflare |
| Primary Color | Buttons, links | JSONB |
| Secondary Color | Accents | JSONB |
| App Name | Title, emails | JSONB |
| Support Email | Footer, errors | JSONB |
| Custom CSS | Advanced styling | JSONB |

**Branding Schema:**
```json
{
  "logo_light_url": "https://...",
  "logo_dark_url": "https://...",
  "favicon_url": "https://...",
  "app_name": "ClientCRM Pro",
  "primary_color": "#3B82F6",
  "secondary_color": "#10B981",
  "support_email": "support@agencydomain.com",
  "custom_css": ".btn-primary { border-radius: 20px; }"
}
```

### 2.3 Custom Domains

**Requirement:** Agencies serve the platform from their own domain.

**Implementation:**
- Agency configures: `app.agencydomain.com`
- DNS: CNAME to our edge (Cloudflare/Vercel)
- SSL: Auto-provisioned via Let's Encrypt
- Routing: Domain → Agency tenant lookup → Serve branded app

**API:**
```
POST /api/agency/domain/add
POST /api/agency/domain/verify
DELETE /api/agency/domain/remove
GET  /api/agency/domain/status
```

### 2.4 Agency Pricing Control

**Requirement:** Agencies set their own pricing for sub-accounts.

**Features:**
- Agency defines custom pricing tiers
- Agency sets usage markup (can exceed platform default)
- Agency receives revenue share or keeps full margin
- Sub-accounts billed through agency's Stripe

**Pricing Override Schema:**
```json
{
  "tiers": [
    {"name": "Basic", "price": 149, "contacts": 2500},
    {"name": "Pro", "price": 299, "contacts": 10000}
  ],
  "usage_markup": {
    "sms": 2.0,
    "email": 3.0,
    "voice": 1.5
  }
}
```

---

## 3. Migration Tools

### 3.1 GoHighLevel Migration

**Requirement:** One-click migration from GHL to capture market share.

**Importable Data:**
| GHL Object | Our Object | Method |
|------------|------------|--------|
| Contacts | Contacts | API |
| Tags | Tags | API |
| Custom Fields | Custom Fields | API |
| Conversations | Conversations | API |
| Workflows | Workflows | Manual rebuild |
| Opportunities | Opportunities | API |
| Pipelines | Pipelines | API |

**Migration Flow:**
1. User provides GHL API key + Location ID
2. System validates credentials
3. Preview: Show counts (X contacts, Y tags, etc.)
4. User confirms
5. Background job imports data in batches
6. Progress updates via WebSocket
7. Completion report with any errors

**API:**
```
POST /api/migration/ghl/connect
GET  /api/migration/ghl/preview
POST /api/migration/ghl/start
GET  /api/migration/ghl/status
```

**GHL API Endpoints Used:**
```
GET /contacts/?locationId={id}
GET /contacts/{id}/tasks
GET /contacts/{id}/notes  
GET /conversations/search?locationId={id}
GET /opportunities/search?location_id={id}
GET /pipelines/?locationId={id}
```

### 3.2 HubSpot Migration

**Requirement:** Import from HubSpot for enterprise prospects.

**Importable Data:**
- Contacts + Companies
- Deals (→ Opportunities)
- Notes + Activities
- Custom Properties

**API:** HubSpot CRM API v3

### 3.3 CSV Import (Enhanced)

**Requirement:** Robust CSV import with mapping UI.

**Features:**
- Upload CSV (up to 500MB)
- Auto-detect columns
- Visual field mapping UI
- Duplicate detection (by email/phone)
- Merge or skip duplicates
- Tag assignment on import
- Workflow trigger on import

---

## 4. 10DLC Registration Wizard

### 4.1 Background

**Requirement:** US A2P SMS requires 10DLC registration through The Campaign Registry (TCR).

**Without 10DLC:**
- Messages blocked or filtered by carriers
- Throughput limited to 1 SMS/second
- Potential fines

**With 10DLC:**
- Full throughput (varies by trust score)
- Better deliverability
- Compliance with carrier requirements

### 4.2 Registration Flow

**Step 1: Brand Registration**
Collect from user:
- Legal Business Name
- DBA (if different)
- EIN / Tax ID
- Business Address
- Website URL
- Vertical (industry)
- Stock Symbol (if public)

**Step 2: Campaign Registration**
For each use case:
- Campaign Description
- Sample Messages (2-5)
- Message Flow (how users opt-in)
- Opt-in Keywords
- Opt-out Keywords
- Help Keywords

**Step 3: Number Assignment**
- Assign phone numbers to campaigns
- Submit to TCR via Twilio API

**Step 4: Verification**
- TCR reviews (1-7 days)
- Trust Score assigned
- Throughput limits set

### 4.3 Implementation

**Data Model:**
```sql
CREATE TABLE tcr_brands (
    id UUID PRIMARY KEY,
    account_id UUID REFERENCES accounts(id),
    twilio_brand_sid VARCHAR(50),
    legal_name VARCHAR(255),
    ein VARCHAR(20),
    status VARCHAR(20), -- 'pending', 'approved', 'rejected'
    trust_score INT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE tcr_campaigns (
    id UUID PRIMARY KEY,
    brand_id UUID REFERENCES tcr_brands(id),
    twilio_campaign_sid VARCHAR(50),
    use_case VARCHAR(100),
    description TEXT,
    sample_messages TEXT[],
    status VARCHAR(20),
    throughput_limit INT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

**UI Wizard:**
- Multi-step form with validation
- Progress indicator
- Save draft capability
- Status dashboard showing all registrations

**API:**
```
POST /api/compliance/10dlc/brand/create
GET  /api/compliance/10dlc/brand/status
POST /api/compliance/10dlc/campaign/create
GET  /api/compliance/10dlc/campaign/status
POST /api/compliance/10dlc/number/assign
```

---

## 5. Local AI / Privacy Options

### 5.1 Requirement

Enterprise customers may not want data sent to OpenAI/Anthropic. Provide self-hosted LLM option.

### 5.2 Supported Providers

| Provider | Type | Use Case |
|----------|------|----------|
| OpenAI | Cloud | Default, best quality |
| Anthropic Claude | Cloud | Alternative cloud |
| Ollama | Local | Privacy-focused |
| vLLM | Self-hosted | Enterprise GPU clusters |
| Custom Endpoint | Any | Bring your own |

### 5.3 Configuration

**AI Provider Settings:**
```json
{
  "provider": "ollama",
  "endpoint": "http://localhost:11434",
  "model": "llama3.1:70b",
  "api_key": null,
  "timeout_ms": 30000,
  "max_tokens": 4096
}
```

**API:**
```
GET  /api/settings/ai/providers
POST /api/settings/ai/configure
POST /api/settings/ai/test
```

### 5.4 Abstraction Layer

All AI calls go through unified interface:
```python
class AIProvider(ABC):
    @abstractmethod
    async def complete(self, prompt: str, **kwargs) -> str:
        pass
    
    @abstractmethod
    async def chat(self, messages: List[dict], **kwargs) -> str:
        pass

class OpenAIProvider(AIProvider): ...
class AnthropicProvider(AIProvider): ...
class OllamaProvider(AIProvider): ...
class CustomProvider(AIProvider): ...
```

---

## 6. Additional Email Requirements

### 6.1 ESP Strategy

**MVP:** Integrate with established providers only.

| Provider | Priority | Use Case |
|----------|----------|----------|
| SendGrid | Primary | Transactional + Marketing |
| Resend | Secondary | Developer-friendly alternative |
| Amazon SES | Enterprise | High volume, cost-effective |
| Mailgun | Backup | Alternative option |

**DO NOT** build custom SMTP infrastructure for MVP.

### 6.2 Deliverability Features

- SPF/DKIM/DMARC setup wizard
- Domain verification UI
- Bounce handling (auto-unsubscribe hard bounces)
- Complaint handling (auto-unsubscribe spam reports)
- Warm-up recommendations for new domains
- Reputation monitoring dashboard

### 6.3 Email Builder

- Drag-and-drop visual builder (MJML-based)
- HTML code editor
- Template library (50+ pre-built)
- Personalization tokens
- Preview (desktop/mobile)
- Spam score checker
- A/B testing (subject, content, send time)

---

## 7. Updated Data Model Summary

```
accounts
├── agencies (if SaaS mode)
│   └── sub_accounts
├── wallets
│   └── wallet_transactions
├── tcr_brands
│   └── tcr_campaigns
├── contacts
├── workflows
├── campaigns
└── settings (including AI provider config)
```

---

## 8. API Additions Summary

| Category | Endpoints |
|----------|-----------|
| Billing | 5 endpoints |
| Wallet | 4 endpoints |
| Agency/White-Label | 8 endpoints |
| Migration | 8 endpoints |
| 10DLC Compliance | 6 endpoints |
| AI Settings | 3 endpoints |
| **Total New** | **34 endpoints** |

---

## 9. Timeline Impact

| Original Estimate | With Addendum | Notes |
|-------------------|---------------|-------|
| MVP: 6-9 months | MVP: 4-6 weeks | Parallel Claude Code execution |
| V1.0: 12-15 months | V1.0: 8-10 weeks | Full feature parity with GHL |
| V2.0: 18+ months | V2.0: 12-16 weeks | Market leadership features |

---

## 10. Risk Mitigation

| Risk | Mitigation |
|------|------------|
| 10DLC delays | Start registration early, use toll-free as backup |
| Email deliverability | Use established ESPs, provide warm-up guidance |
| Billing complexity | Use Stripe Billing for subscriptions, custom for usage |
| Migration failures | Robust error handling, manual fallback options |
| AI provider outages | Support multiple providers, graceful degradation |

---

*Addendum v1.0 - Ziloss Technologies*
*Ready for implementation*
