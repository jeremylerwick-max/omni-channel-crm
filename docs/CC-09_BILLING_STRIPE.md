# CC-09: Billing & Stripe Integration
## Claude Code Task Specification

**Module:** Subscription + Usage-Based Billing
**Priority:** P0 (MVP Critical)
**Estimated Time:** 3-4 days
**Dependencies:** None

---

## Objective

Implement Stripe subscription billing with usage-based wallet system for SMS/email/voice credits.

---

## Directory Structure
```
backend/modules/billing/
├── __init__.py
├── service.py           # Main billing service
├── stripe_client.py     # Stripe API wrapper
├── wallet.py            # Usage wallet system
├── subscriptions.py     # Subscription management
├── invoices.py          # Invoice generation
├── webhooks.py          # Stripe webhooks
├── dunning.py           # Failed payment handling
└── tests/
```

---

## Database Schema
```sql
-- backend/schema/024_billing.sql

CREATE TABLE subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id UUID NOT NULL UNIQUE,
    stripe_customer_id VARCHAR(100),
    stripe_subscription_id VARCHAR(100),
    plan VARCHAR(50) NOT NULL,  -- starter, professional, agency, enterprise
    status VARCHAR(20) DEFAULT 'active',  -- active, past_due, canceled, paused
    current_period_start TIMESTAMPTZ,
    current_period_end TIMESTAMPTZ,
    cancel_at_period_end BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE wallets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id UUID NOT NULL UNIQUE,
    balance DECIMAL(10,4) DEFAULT 0,
    auto_recharge BOOLEAN DEFAULT TRUE,
    recharge_threshold DECIMAL(10,2) DEFAULT 10.00,
    recharge_amount DECIMAL(10,2) DEFAULT 50.00,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE wallet_transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    wallet_id UUID REFERENCES wallets(id),
    type VARCHAR(20) NOT NULL,  -- credit, debit, refund
    amount DECIMAL(10,4) NOT NULL,
    resource_type VARCHAR(50),  -- sms, email, voice, ai
    resource_id VARCHAR(255),
    description TEXT,
    balance_after DECIMAL(10,4),
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## Pricing Configuration
```python
PLANS = {
    "starter": {
        "price_monthly": 97,
        "stripe_price_id": "price_xxx",
        "contacts": 5000,
        "users": 3,
        "features": ["crm", "sms", "email"]
    },
    "professional": {
        "price_monthly": 297,
        "stripe_price_id": "price_xxx",
        "contacts": 25000,
        "users": 10,
        "features": ["crm", "sms", "email", "workflows", "ai_testing"]
    },
    "agency": {
        "price_monthly": 497,
        "stripe_price_id": "price_xxx",
        "contacts": 100000,
        "users": -1,  # Unlimited
        "features": ["all", "white_label", "sub_accounts"]
    }
}

USAGE_PRICING = {
    "sms_outbound": 0.012,
    "sms_inbound": 0.012,
    "mms_outbound": 0.03,
    "voice_minute": 0.021,
    "email": 0.0002,
    "ai_tokens_1k": 0.006
}
```

---

## API Endpoints
```
POST   /api/billing/subscribe             # Create subscription
POST   /api/billing/upgrade               # Change plan
POST   /api/billing/cancel                # Cancel subscription
GET    /api/billing/subscription          # Current subscription
GET    /api/billing/invoices              # Invoice history
GET    /api/billing/usage                 # Usage summary

GET    /api/wallet/balance                # Current balance
POST   /api/wallet/add-funds              # Add credits
GET    /api/wallet/transactions           # Transaction history
POST   /api/wallet/auto-recharge          # Configure auto-recharge

POST   /api/webhooks/stripe               # Stripe webhooks
```

---

## Dunning Flow

1. Payment fails → Retry 24h
2. Second fail → Email warning, retry 48h
3. Third fail → Pause workflows, show banner
4. Day 7 → Downgrade to free, retain data
5. Day 30 → Archive account

---

## Acceptance Criteria

1. ✅ Stripe Checkout for new subscriptions
2. ✅ Plan upgrades/downgrades
3. ✅ Subscription cancellation
4. ✅ Wallet credit/debit for usage
5. ✅ Auto-recharge when low
6. ✅ Stripe webhook handling
7. ✅ Dunning for failed payments
8. ✅ Usage reporting dashboard
9. ✅ 85%+ test coverage
