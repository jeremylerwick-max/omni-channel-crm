# Claude Code Ready-to-Paste Prompts

Copy-paste these into separate Claude Code terminal sessions.

---

## CC-01: Email Service (P0)

```
PROJECT: Omni-Channel CRM
REPO: /Users/mac/Desktop/omni-channel-crm

READ THE SPEC:
/Users/mac/Desktop/omni-channel-crm/specs/CC-01_EMAIL_SERVICE.md

CONTEXT:
- Backend at /backend/app/
- Existing models in /backend/app/models/ (base.py, messaging.py, workflow.py, billing.py)
- Routes go in /backend/app/api/routes/
- Services go in /backend/app/services/ (create this dir)
- Database: PostgreSQL async via SQLAlchemy (see /backend/app/core/database.py)
- Config pattern: see /backend/app/core/config.py

YOUR TASK:
1. Create /backend/app/services/email/ directory with all files from spec
2. Create /backend/app/models/email.py with EmailDomain, EmailTemplate, EmailSend models
3. Create /backend/app/api/routes/email.py with all endpoints
4. Add email models to /backend/app/models/__init__.py
5. Register email router in /backend/app/api/routes/__init__.py
6. Add SendGrid webhook handler to /backend/app/api/routes/webhooks.py
7. Write tests in /backend/tests/test_email.py

PATTERNS TO FOLLOW:
- Look at /backend/app/api/routes/contacts.py for route patterns
- Look at /backend/app/models/base.py for model patterns
- Use async/await everywhere
- Pydantic for request/response schemas
- Type hints on all functions

ENV VARS (already in config.py):
- SENDGRID_API_KEY
- SENDGRID_FROM_EMAIL

RUN WHEN DONE:
cd /Users/mac/Desktop/omni-channel-crm/backend && pip install sendgrid resend && pytest tests/test_email.py -v

BUILD IT.
```

---

## CC-03: Workflow Engine v2 (P0)

```
PROJECT: Omni-Channel CRM
REPO: /Users/mac/Desktop/omni-channel-crm

READ THE SPEC:
/Users/mac/Desktop/omni-channel-crm/specs/CC-03_WORKFLOW_ENGINE.md

CONTEXT:
- Backend at /backend/app/
- Existing Workflow model in /backend/app/models/workflow.py
- Existing workflow routes in /backend/app/api/routes/workflows.py
- There's old workflow code in /backend/modules/workflow_engine/ - IGNORE IT, build fresh

YOUR TASK:
1. Create /backend/app/services/workflow/ with:
   - engine.py (main executor)
   - parser.py (YAML/JSON parsing)
   - scheduler.py (delay handling)
   - triggers.py (event triggers)
   - state.py (state machine)
   - actions/ directory with all action classes

2. Add WorkflowExecution model to /backend/app/models/workflow.py

3. Expand /backend/app/api/routes/workflows.py with:
   - POST /{id}/import (import definition)
   - GET /{id}/export (export definition)
   - POST /{id}/test (dry-run)
   - GET /{id}/enrollments

4. Create /backend/app/workers/workflow_worker.py (background processor)

5. Write tests in /backend/tests/test_workflow_engine.py

KEY REQUIREMENTS:
- YAML and JSON workflow definitions must both work
- Delays schedule via next_action_at field
- Conditions evaluate and branch correctly
- All actions use the WorkflowAction base class
- Actions: send_sms, send_email, add_tag, remove_tag, update_field, delay, condition, ab_split

PATTERNS:
- Async everywhere
- Use existing database session pattern from get_db()
- Actions should be easily extensible

RUN WHEN DONE:
cd /Users/mac/Desktop/omni-channel-crm/backend && pip install pyyaml && pytest tests/test_workflow_engine.py -v

BUILD IT.
```

---

## CC-06: AI Testing Layer (P0 - KILLER FEATURE)

```
PROJECT: Omni-Channel CRM
REPO: /Users/mac/Desktop/omni-channel-crm

READ THE SPEC:
/Users/mac/Desktop/omni-channel-crm/specs/CC-06_AI_TESTING.md

THIS IS THE KILLER FEATURE - NO COMPETITOR HAS THIS.

CONTEXT:
- Backend at /backend/app/
- Workflow models in /backend/app/models/workflow.py
- AI config in /backend/app/core/config.py (ANTHROPIC_API_KEY, OPENAI_API_KEY, OLLAMA settings)
- Depends on workflow engine (can stub if needed)

YOUR TASK:
1. Create /backend/app/services/ai_testing/ with:
   - simulator.py (main simulation engine)
   - personas.py (AI persona management)
   - validator.py (workflow validation)
   - reporter.py (test report generation)
   - providers/ (anthropic.py, openai.py, ollama.py)

2. Create /backend/app/models/ai_testing.py with:
   - TestPersona
   - WorkflowTest
   - TestInteraction
   - TestReport

3. Create /backend/app/api/routes/ai_testing.py with:
   - GET/POST /personas
   - POST /workflows/{id}/test
   - GET /tests/{id}
   - GET /tests/{id}/report
   - POST /workflows/{id}/validate

4. Add 7 default personas as seed data:
   - Eager Eddie (quick buyer)
   - Skeptical Sarah (needs convincing)
   - Busy Bob (rarely responds)
   - Chatty Cathy (verbose)
   - Cold Carl (tests opt-out)
   - Price-Conscious Pam (asks about cost)
   - Technical Tim (wants specs)

5. Write tests in /backend/tests/test_ai_testing.py

KEY REQUIREMENTS:
- AI simulates a lead receiving marketing messages
- AI responds in-character based on persona
- Simulation walks through entire workflow
- Validator checks for spam triggers, infinite loops, orphan steps
- Report gives actionable recommendations

AI PROVIDER PATTERN:
```python
class AIProvider(ABC):
    @abstractmethod
    async def complete(self, prompt: str) -> str:
        pass
```

Use Anthropic as default, fallback to OpenAI, then Ollama.

RUN WHEN DONE:
cd /Users/mac/Desktop/omni-channel-crm/backend && pip install anthropic openai && pytest tests/test_ai_testing.py -v

BUILD IT.
```

---

## CC-05: Visual Workflow Builder (P0)

```
PROJECT: Omni-Channel CRM
REPO: /Users/mac/Desktop/omni-channel-crm

READ THE SPEC:
/Users/mac/Desktop/omni-channel-crm/specs/CC-05_VISUAL_BUILDER.md

CONTEXT:
- Frontend at /frontend/
- Existing React setup with Vite, TypeScript, TailwindCSS
- Package.json exists, may need updates
- Backend workflow API at /api/v1/workflows/

YOUR TASK:
1. Install dependencies:
   npm install reactflow zustand lucide-react

2. Create /frontend/src/components/workflow-builder/:
   - WorkflowCanvas.tsx (main React Flow canvas)
   - NodePalette.tsx (draggable action list)
   - nodes/ (TriggerNode, SendSMSNode, SendEmailNode, DelayNode, ConditionNode, AddTagNode, WebhookNode, EndNode)
   - edges/ConditionalEdge.tsx
   - panels/NodeConfigPanel.tsx
   - panels/WorkflowSettings.tsx
   - hooks/useWorkflowStore.ts

3. Create /frontend/src/lib/workflow-converter.ts:
   - canvasToDefinition() - React Flow → JSON
   - definitionToCanvas() - JSON → React Flow

4. Create /frontend/src/pages/WorkflowBuilderPage.tsx

5. Add route in App.tsx: /workflows/:id/edit → WorkflowBuilderPage

REQUIREMENTS:
- Drag nodes from palette to canvas
- Connect nodes with edges
- Condition node has Yes/No output handles
- Config panel appears when node selected
- Save button calls PUT /api/v1/workflows/{id}
- Load existing workflow on page load

STYLING:
- Use TailwindCSS
- Clean, modern look
- Node colors by type (green=SMS, blue=email, yellow=condition, etc.)

RUN WHEN DONE:
cd /Users/mac/Desktop/omni-channel-crm/frontend && npm install && npm run dev

BUILD IT.
```

---

## CC-09: Billing & Stripe (P1)

```
PROJECT: Omni-Channel CRM
REPO: /Users/mac/Desktop/omni-channel-crm

READ THE SPEC:
/Users/mac/Desktop/omni-channel-crm/specs/CC-09_BILLING.md

CONTEXT:
- Backend at /backend/app/
- Existing billing models in /backend/app/models/billing.py (Wallet, WalletTransaction, Subscription)
- Stripe config in /backend/app/core/config.py

YOUR TASK:
1. Create /backend/app/services/billing/:
   - stripe_service.py (Stripe API wrapper)
   - wallet_service.py (usage tracking/debits)
   - subscription.py (tier management)
   - dunning.py (failed payment handling)

2. Create /backend/app/api/routes/billing.py:
   - POST /subscribe
   - POST /upgrade
   - POST /downgrade  
   - POST /cancel
   - GET /subscription
   - GET /invoices
   - GET /wallet
   - POST /wallet/add-funds
   - GET /wallet/transactions
   - POST /wallet/auto-recharge

3. Add Stripe webhook handler to /backend/app/api/routes/webhooks.py:
   - invoice.payment_succeeded
   - invoice.payment_failed
   - customer.subscription.deleted

4. Write tests in /backend/tests/test_billing.py

PRICING (hardcode these):
- Starter: $97/mo, 5k contacts, 3 users
- Professional: $297/mo, 25k contacts, 10 users
- Agency: $497/mo, 100k contacts, unlimited users

USAGE COSTS:
- SMS: $0.012 per message
- Email: $0.0002 per email
- Voice: $0.021 per minute
- AI: $0.006 per 1K tokens

RUN WHEN DONE:
cd /Users/mac/Desktop/omni-channel-crm/backend && pip install stripe && pytest tests/test_billing.py -v

BUILD IT.
```

---

## CC-02: Voice Service (P1)

```
PROJECT: Omni-Channel CRM  
REPO: /Users/mac/Desktop/omni-channel-crm

READ THE SPEC:
/Users/mac/Desktop/omni-channel-crm/specs/CC-02_VOICE_SERVICE.md

CONTEXT:
- Backend at /backend/app/
- Twilio already configured (TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN in config)
- Existing Twilio SMS code in /backend/modules/twilio_sms/ for reference

YOUR TASK:
1. Create /backend/app/services/voice/:
   - service.py (main voice service)
   - voicemail.py (voicemail drop)
   - transcription.py (call transcription)

2. Create /backend/app/models/voice.py:
   - Call model (id, contact_id, direction, status, duration, recording_url, transcription, twilio_sid)

3. Create /backend/app/api/routes/voice.py:
   - POST /call (initiate outbound call)
   - POST /voicemail (drop voicemail)
   - GET /calls (list calls)
   - GET /calls/{id} (get call details)

4. Add Twilio Voice webhooks to /backend/app/api/routes/webhooks.py:
   - /twilio/voice/status
   - /twilio/voice/recording

5. Write tests in /backend/tests/test_voice.py

RUN WHEN DONE:
cd /Users/mac/Desktop/omni-channel-crm/backend && pytest tests/test_voice.py -v

BUILD IT.
```

---

## Quick Reference

| Module | Command to Start |
|--------|------------------|
| CC-01 Email | `claude` then paste CC-01 prompt |
| CC-02 Voice | `claude` then paste CC-02 prompt |
| CC-03 Workflow | `claude` then paste CC-03 prompt |
| CC-05 Visual | `claude` then paste CC-05 prompt |
| CC-06 AI Test | `claude` then paste CC-06 prompt |
| CC-09 Billing | `claude` then paste CC-09 prompt |

Run these in parallel terminal tabs for max speed.
