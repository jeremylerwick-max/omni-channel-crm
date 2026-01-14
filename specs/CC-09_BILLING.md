# CC-09: Billing & Stripe Integration

## Overview
Stripe subscriptions + usage-based wallet for SMS/email/voice costs.

## Repository
`/Users/mac/Desktop/omni-channel-crm`

## Files to Create

```
backend/app/services/billing/
├── __init__.py
├── stripe_service.py    # Stripe API wrapper
├── wallet_service.py    # Usage wallet
├── subscription.py      # Subscription management
└── dunning.py          # Failed payment handling
```

## Pricing Tiers

| Tier | Price | Contacts | Users | Features |
|------|-------|----------|-------|----------|
| Starter | $97/mo | 5,000 | 3 | CRM, SMS, Email |
| Professional | $297/mo | 25,000 | 10 | + Workflows, AI |
| Agency | $497/mo | 100,000 | ∞ | + White-Label |

## Usage Costs (Wallet)

| Resource | Our Cost | Markup | User Pays |
|----------|----------|--------|-----------|
| SMS Out | $0.0079 | 50% | $0.012 |
| SMS In | $0.0079 | 50% | $0.012 |
| Voice/min | $0.014 | 50% | $0.021 |
| Email | $0.0001 | 100% | $0.0002 |
| AI Token (1K) | $0.003 | 100% | $0.006 |

## API Endpoints

```python
# Subscriptions
POST   /api/v1/billing/subscribe
POST   /api/v1/billing/upgrade
POST   /api/v1/billing/downgrade
POST   /api/v1/billing/cancel
GET    /api/v1/billing/subscription
GET    /api/v1/billing/invoices

# Wallet
GET    /api/v1/billing/wallet
POST   /api/v1/billing/wallet/add-funds
GET    /api/v1/billing/wallet/transactions
POST   /api/v1/billing/wallet/auto-recharge

# Webhooks
POST   /api/v1/webhooks/stripe
```

## Stripe Service

```python
# backend/app/services/billing/stripe_service.py

import stripe
from app.core.config import settings

stripe.api_key = settings.STRIPE_SECRET_KEY

class StripeService:
    PRICE_IDS = {
        "starter": "price_starter_monthly",
        "professional": "price_pro_monthly",
        "agency": "price_agency_monthly",
    }
    
    async def create_customer(self, email: str, name: str) -> str:
        customer = stripe.Customer.create(email=email, name=name)
        return customer.id
    
    async def create_subscription(
        self, 
        customer_id: str, 
        tier: str
    ) -> dict:
        subscription = stripe.Subscription.create(
            customer=customer_id,
            items=[{"price": self.PRICE_IDS[tier]}],
            payment_behavior="default_incomplete",
            expand=["latest_invoice.payment_intent"],
        )
        return {
            "subscription_id": subscription.id,
            "client_secret": subscription.latest_invoice.payment_intent.client_secret,
        }
    
    async def cancel_subscription(self, subscription_id: str):
        stripe.Subscription.delete(subscription_id)
    
    async def charge_usage(
        self, 
        customer_id: str, 
        amount: int, 
        description: str
    ):
        stripe.InvoiceItem.create(
            customer=customer_id,
            amount=amount,  # in cents
            currency="usd",
            description=description,
        )
```

## Wallet Service

```python
# backend/app/services/billing/wallet_service.py

from decimal import Decimal
from app.models import Wallet, WalletTransaction

USAGE_COSTS = {
    "sms_outbound": Decimal("0.012"),
    "sms_inbound": Decimal("0.012"),
    "voice_minute": Decimal("0.021"),
    "email": Decimal("0.0002"),
    "ai_tokens_1k": Decimal("0.006"),
}

class WalletService:
    def __init__(self, db_session):
        self.db = db_session
    
    async def get_balance(self, account_id: str) -> Decimal:
        wallet = await self.get_wallet(account_id)
        return wallet.balance
    
    async def debit(
        self, 
        account_id: str, 
        resource_type: str,
        resource_id: str,
        quantity: int = 1
    ) -> bool:
        wallet = await self.get_wallet(account_id)
        cost = USAGE_COSTS.get(resource_type, Decimal("0")) * quantity
        
        if wallet.balance < cost:
            # Check auto-recharge
            if wallet.auto_recharge:
                await self.auto_recharge(wallet)
            else:
                return False
        
        wallet.balance -= cost
        
        # Log transaction
        tx = WalletTransaction(
            wallet_id=wallet.id,
            type="debit",
            amount=-cost,
            resource_type=resource_type,
            resource_id=resource_id,
            balance_after=wallet.balance,
        )
        self.db.add(tx)
        
        return True
    
    async def credit(
        self, 
        account_id: str, 
        amount: Decimal,
        description: str
    ):
        wallet = await self.get_wallet(account_id)
        wallet.balance += amount
        
        tx = WalletTransaction(
            wallet_id=wallet.id,
            type="credit",
            amount=amount,
            description=description,
            balance_after=wallet.balance,
        )
        self.db.add(tx)
    
    async def auto_recharge(self, wallet: Wallet):
        if wallet.balance < wallet.recharge_threshold:
            # Charge Stripe
            stripe_service = StripeService()
            # ... charge customer
            
            # Credit wallet
            await self.credit(
                wallet.account_id,
                wallet.recharge_amount,
                "Auto-recharge"
            )
```

## Dunning (Failed Payments)

```python
# backend/app/services/billing/dunning.py

from datetime import datetime, timedelta

class DunningService:
    async def handle_failed_payment(self, subscription_id: str):
        subscription = await self.get_subscription(subscription_id)
        subscription.failed_payment_count += 1
        subscription.last_payment_attempt = datetime.utcnow()
        
        if subscription.failed_payment_count == 1:
            # First failure: retry in 24h
            await self.schedule_retry(subscription, hours=24)
            
        elif subscription.failed_payment_count == 2:
            # Second: email warning, retry in 48h
            await self.send_payment_warning(subscription)
            await self.schedule_retry(subscription, hours=48)
            
        elif subscription.failed_payment_count == 3:
            # Third: pause automations
            await self.pause_account(subscription.account_id)
            await self.send_final_warning(subscription)
            
        elif subscription.failed_payment_count >= 4:
            # Fourth: downgrade to free
            await self.downgrade_to_free(subscription.account_id)
```

## Webhook Handler

```python
# Add to backend/app/api/routes/webhooks.py

@router.post("/stripe")
async def stripe_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    
    event = stripe.Webhook.construct_event(
        payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
    )
    
    if event["type"] == "invoice.payment_succeeded":
        # Update subscription status
        pass
    elif event["type"] == "invoice.payment_failed":
        # Trigger dunning flow
        dunning = DunningService(db)
        await dunning.handle_failed_payment(
            event["data"]["object"]["subscription"]
        )
    elif event["type"] == "customer.subscription.deleted":
        # Mark subscription canceled
        pass
    
    return {"received": True}
```

## Success Criteria

- [ ] Stripe customer creation
- [ ] Subscription creation (all tiers)
- [ ] Subscription upgrade/downgrade
- [ ] Subscription cancellation
- [ ] Wallet balance tracking
- [ ] Usage debit (SMS, email, voice, AI)
- [ ] Auto-recharge functionality
- [ ] Dunning flow (4 stages)
- [ ] Stripe webhook handling
- [ ] Transaction history
- [ ] Invoice listing
