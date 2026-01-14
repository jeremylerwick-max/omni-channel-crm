# CC-04: API Framework Expansion

**Priority:** P1 | **Time:** 2 days

Expand API with full CRUD for all entities, webhooks, API keys, rate limiting.

```
POST   /api/api-keys                # Create API key
GET    /api/api-keys                # List keys
DELETE /api/api-keys/{id}           # Revoke key
POST   /api/webhooks                # Create webhook endpoint
GET    /api/webhooks                # List webhooks
PUT    /api/webhooks/{id}           # Update webhook
DELETE /api/webhooks/{id}           # Delete webhook
GET    /api/webhooks/{id}/logs      # Webhook delivery logs
```

---

# CC-07: Segmentation Engine

**Priority:** P1 | **Time:** 2-3 days

Dynamic list builder with complex filters (AND/OR), behaviors, date ranges.

```sql
CREATE TABLE segments (
    id UUID PRIMARY KEY,
    name VARCHAR(255),
    filters JSONB NOT NULL,  -- Complex filter tree
    is_dynamic BOOLEAN DEFAULT TRUE,
    cached_count INT,
    last_computed TIMESTAMPTZ
);
```

Filter format:
```json
{
  "operator": "AND",
  "conditions": [
    {"field": "tags", "op": "contains", "value": "hot-lead"},
    {"field": "last_email_opened", "op": "within", "value": "7d"},
    {
      "operator": "OR",
      "conditions": [
        {"field": "state", "op": "equals", "value": "CA"},
        {"field": "state", "op": "equals", "value": "TX"}
      ]
    }
  ]
}
```

---

# CC-08: Pipeline/Opportunity CRM

**Priority:** P2 | **Time:** 2 days

Sales pipelines with stages, opportunities, and deal tracking.

```sql
CREATE TABLE pipelines (
    id UUID PRIMARY KEY,
    name VARCHAR(255),
    stages JSONB NOT NULL  -- Ordered list of stages
);

CREATE TABLE opportunities (
    id UUID PRIMARY KEY,
    pipeline_id UUID REFERENCES pipelines(id),
    contact_id UUID REFERENCES contacts(id),
    stage VARCHAR(100),
    value DECIMAL(12,2),
    status VARCHAR(20),  -- open, won, lost
    expected_close DATE,
    notes TEXT
);
```

---

# CC-11: Analytics Dashboard

**Priority:** P2 | **Time:** 3 days

Metrics dashboards for campaigns, SMS, email, voice with charts.

Key metrics:
- Contacts added (today/week/month)
- SMS sent/delivered/replied
- Emails sent/opened/clicked
- Calls made/answered/voicemail
- Workflow enrollments/completions
- Conversion rates by source

Use Recharts for visualization.

---

# CC-12: User Roles/RBAC

**Priority:** P2 | **Time:** 2 days

Role-based access control with permissions.

```sql
CREATE TABLE roles (
    id UUID PRIMARY KEY,
    name VARCHAR(100),
    permissions JSONB NOT NULL
);

CREATE TABLE user_roles (
    user_id UUID REFERENCES users(id),
    role_id UUID REFERENCES roles(id),
    PRIMARY KEY (user_id, role_id)
);
```

Default roles: Admin, Manager, Agent, ReadOnly

---

# CC-14: 10DLC Registration Wizard

**Priority:** P2 | **Time:** 2-3 days

Multi-step form for TCR brand/campaign registration via Twilio.

Steps:
1. Business info (EIN, address, vertical)
2. Campaign details (use case, sample messages)
3. Submit to Twilio → TCR
4. Status tracking dashboard

---

# CC-15: Phase 6 UI

**Priority:** P0 | **Time:** 3 days

Dashboard, Inbox, Contact detail pages (see CLAUDE_CODE_TASK_PHASE6.md in agent-orchestrator)

Key components:
- DashboardPage with metrics cards
- ConversationsPage with contact names
- Contact detail with tags, timeline
- Cmd+K command palette
