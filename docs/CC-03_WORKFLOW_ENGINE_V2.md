# CC-03: Workflow Engine v2
## Claude Code Task Specification

**Module:** Code-Driven Workflow Engine
**Priority:** P0 (MVP Critical)
**Estimated Time:** 4-5 days
**Dependencies:** Existing workflow_engine v1

---

## Objective

Upgrade workflow engine to support YAML/JSON configs, advanced branching, A/B testing, and visual builder parity.

---

## Technical Requirements

### 1. Directory Structure
```
backend/modules/workflow_engine_v2/
├── __init__.py
├── models.py              # Pydantic workflow models
├── parser.py              # YAML/JSON parser
├── executor.py            # Workflow execution engine
├── state_machine.py       # State management
├── triggers/
│   ├── __init__.py
│   ├── base.py            # Trigger interface
│   ├── contact.py         # Contact triggers (created, tagged, etc)
│   ├── message.py         # SMS/email received triggers
│   ├── webhook.py         # External webhook triggers
│   ├── schedule.py        # Time-based triggers
│   └── manual.py          # Manual enrollment
├── actions/
│   ├── __init__.py
│   ├── base.py            # Action interface
│   ├── sms.py             # Send SMS action
│   ├── email.py           # Send email action
│   ├── voice.py           # Make call action
│   ├── contact.py         # Update contact, add tag
│   ├── webhook.py         # HTTP request action
│   ├── wait.py            # Delay action
│   ├── branch.py          # If/else branching
│   ├── ab_split.py        # A/B testing
│   └── goal.py            # Goal/conversion tracking
├── conditions/
│   ├── __init__.py
│   ├── contact.py         # Contact field conditions
│   ├── behavior.py        # Opened email, clicked, etc
│   └── custom.py          # Custom expression evaluator
├── scheduler.py           # Delayed action scheduler
├── api.py                 # FastAPI routes
└── tests/
    ├── test_parser.py
    ├── test_executor.py
    ├── test_triggers.py
    └── test_actions.py
```

### 2. Database Schema
```sql
-- backend/schema/022_workflow_engine_v2.sql

CREATE TABLE workflows_v2 (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    location_id UUID NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(20) DEFAULT 'draft',  -- draft, active, paused, archived
    trigger_type VARCHAR(50) NOT NULL,
    trigger_config JSONB NOT NULL,
    definition JSONB NOT NULL,           -- Full workflow definition
    yaml_source TEXT,                    -- Original YAML if imported
    version INT DEFAULT 1,
    stats JSONB DEFAULT '{"enrolled": 0, "completed": 0, "active": 0}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    published_at TIMESTAMPTZ
);

CREATE TABLE workflow_enrollments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id UUID REFERENCES workflows_v2(id),
    contact_id UUID REFERENCES contacts(id),
    status VARCHAR(20) DEFAULT 'active',  -- active, completed, exited, failed
    current_step VARCHAR(100),
    step_data JSONB DEFAULT '{}',         -- Data accumulated through workflow
    enrolled_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    exit_reason TEXT,
    UNIQUE(workflow_id, contact_id)
);

CREATE TABLE workflow_step_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    enrollment_id UUID REFERENCES workflow_enrollments(id),
    step_id VARCHAR(100) NOT NULL,
    step_type VARCHAR(50) NOT NULL,
    status VARCHAR(20),  -- pending, executing, completed, failed, skipped
    input_data JSONB,
    output_data JSONB,
    error TEXT,
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

CREATE TABLE workflow_scheduled_actions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    enrollment_id UUID REFERENCES workflow_enrollments(id),
    step_id VARCHAR(100) NOT NULL,
    scheduled_for TIMESTAMPTZ NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_enrollments_workflow ON workflow_enrollments(workflow_id);
CREATE INDEX idx_enrollments_contact ON workflow_enrollments(contact_id);
CREATE INDEX idx_enrollments_status ON workflow_enrollments(status);
CREATE INDEX idx_scheduled_pending ON workflow_scheduled_actions(scheduled_for) 
    WHERE status = 'pending';
```

### 3. YAML Workflow Format
```yaml
# Example workflow definition
name: New Lead Nurture
description: Welcome sequence for new leads
version: 1

trigger:
  type: contact_created
  filters:
    - field: tags
      operator: contains
      value: "new-lead"

steps:
  - id: welcome_email
    type: send_email
    config:
      template_id: "{{templates.welcome}}"
      delay: 0
    
  - id: wait_1_day
    type: wait
    config:
      duration: 1d
      business_hours_only: false
      
  - id: check_opened
    type: condition
    config:
      if:
        - field: "{{steps.welcome_email.opened}}"
          operator: equals
          value: true
      then: send_followup_sms
      else: send_reminder_email
      
  - id: send_followup_sms
    type: send_sms
    config:
      message: "Hi {{contact.first_name}}, did you get a chance to read our welcome email?"
      
  - id: send_reminder_email
    type: send_email
    config:
      template_id: "{{templates.reminder}}"
      
  - id: ab_test
    type: ab_split
    config:
      variants:
        - name: A
          weight: 50
          next: call_immediately
        - name: B
          weight: 50
          next: wait_then_call
          
  - id: call_immediately
    type: make_call
    config:
      voicemail_drop_id: "{{voicemails.intro}}"
      
  - id: wait_then_call
    type: wait
    config:
      duration: 2d
    next: call_immediately
    
  - id: goal_check
    type: goal
    config:
      condition:
        field: tags
        operator: contains
        value: "booked-appointment"
      on_success: exit_success
      timeout: 7d
      on_timeout: exit_timeout
```

### 4. Workflow Executor
```python
# backend/modules/workflow_engine_v2/executor.py

class WorkflowExecutor:
    async def enroll_contact(
        self, 
        workflow_id: str, 
        contact_id: str,
        initial_data: dict = None
    ) -> str:
        """Enroll contact in workflow, return enrollment_id"""
        pass
    
    async def execute_step(
        self, 
        enrollment_id: str, 
        step_id: str
    ) -> StepResult:
        """Execute a single step, return result with next step"""
        pass
    
    async def process_enrollment(self, enrollment_id: str):
        """Process all pending steps for enrollment"""
        pass
    
    async def check_conditions(
        self, 
        conditions: List[Condition], 
        context: dict
    ) -> bool:
        """Evaluate condition expressions"""
        pass
    
    async def schedule_delayed_action(
        self, 
        enrollment_id: str,
        step_id: str,
        delay: timedelta
    ):
        """Schedule future step execution"""
        pass
```

### 5. API Endpoints
```
POST   /api/workflows                     # Create workflow
GET    /api/workflows                     # List workflows
GET    /api/workflows/{id}                # Get workflow
PUT    /api/workflows/{id}                # Update workflow
DELETE /api/workflows/{id}                # Delete workflow
POST   /api/workflows/{id}/publish        # Activate workflow
POST   /api/workflows/{id}/pause          # Pause workflow
POST   /api/workflows/import              # Import YAML
GET    /api/workflows/{id}/export         # Export as YAML
POST   /api/workflows/{id}/enroll         # Manually enroll contact
GET    /api/workflows/{id}/enrollments    # List enrollments
GET    /api/workflows/{id}/stats          # Workflow analytics
POST   /api/workflows/{id}/test           # Test with AI (CC-06)
GET    /api/enrollments/{id}              # Enrollment details
POST   /api/enrollments/{id}/exit         # Force exit enrollment
GET    /api/enrollments/{id}/logs         # Step execution logs
```

### 6. Background Workers
```python
# Two workers needed:

# 1. Scheduled Action Processor
async def process_scheduled_actions():
    """Run every minute, execute due scheduled actions"""
    due_actions = await get_due_scheduled_actions()
    for action in due_actions:
        await execute_step(action.enrollment_id, action.step_id)

# 2. Trigger Listener
async def listen_for_triggers():
    """Subscribe to events and trigger workflows"""
    # Redis pub/sub or database polling
    # Events: contact_created, tag_added, sms_received, etc.
```

---

## Acceptance Criteria

1. ✅ Parse YAML workflow definitions
2. ✅ Parse JSON workflow definitions
3. ✅ All trigger types working
4. ✅ All action types working
5. ✅ Conditional branching (if/else)
6. ✅ A/B split testing
7. ✅ Delayed actions with scheduler
8. ✅ Goal tracking with timeout
9. ✅ Contact can only be in workflow once
10. ✅ Exit conditions
11. ✅ Step logging for debugging
12. ✅ Import/export YAML
13. ✅ Workflow versioning
14. ✅ 90%+ test coverage

---

## Integration Points

- **Email Service (CC-01):** send_email action
- **Voice Module (CC-02):** make_call action
- **Twilio SMS:** send_sms action (existing)
- **CRM Core:** contact triggers and updates
- **Visual Builder (CC-05):** Must export compatible JSON
- **AI Testing (CC-06):** Test endpoint for validation

---

## Variable System

```python
# Available variables in templates/configs:
{{contact.first_name}}
{{contact.last_name}}
{{contact.email}}
{{contact.phone}}
{{contact.tags}}
{{contact.custom_fields.xxx}}

{{steps.<step_id>.result}}
{{steps.<step_id>.opened}}      # For emails
{{steps.<step_id>.clicked}}     # For emails
{{steps.<step_id>.replied}}     # For SMS

{{workflow.name}}
{{workflow.enrolled_at}}
{{now}}
{{now|add_days:3}}
```
