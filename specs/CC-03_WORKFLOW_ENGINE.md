# CC-03: Workflow Engine v2

## Overview
Build a code-driven workflow engine supporting YAML/JSON definitions, state machine execution, and trigger-based automation.

## Repository
`/Users/mac/Desktop/omni-channel-crm`

## Priority
**P0 - Core Feature** - This is the heart of the automation platform.

## Files to Create

```
backend/app/services/workflow/
├── __init__.py
├── engine.py           # Main workflow executor
├── parser.py           # YAML/JSON → workflow graph
├── scheduler.py        # Delay/timing management
├── triggers.py         # Event triggers
├── actions/
│   ├── __init__.py
│   ├── base.py         # Action interface
│   ├── messaging.py    # SMS/Email actions
│   ├── crm.py          # Tag/field update actions
│   ├── logic.py        # Conditions, splits, waits
│   └── http.py         # Webhook/API call actions
└── state.py            # State machine management
```

## Workflow Definition Schema

```yaml
# Example workflow definition
name: New Lead Welcome Sequence
version: 1
trigger:
  type: contact_created
  conditions:
    - field: source
      operator: equals
      value: "facebook_ad"

steps:
  - id: send_welcome_sms
    type: send_sms
    config:
      template: welcome_sms
      
  - id: wait_1_day
    type: delay
    config:
      duration: 1
      unit: days
      
  - id: check_reply
    type: condition
    config:
      field: last_sms_reply
      operator: exists
    branches:
      true: send_followup_email
      false: send_reminder_sms
      
  - id: send_followup_email
    type: send_email
    config:
      template: followup_email
    next: end
    
  - id: send_reminder_sms
    type: send_sms
    config:
      template: reminder_sms
    next: wait_2_days
    
  - id: wait_2_days
    type: delay
    config:
      duration: 2
      unit: days
    next: add_cold_tag
    
  - id: add_cold_tag
    type: add_tag
    config:
      tag: "cold_lead"
```

## JSON Schema

```json
{
  "name": "New Lead Welcome",
  "version": 1,
  "trigger": {
    "type": "tag_added",
    "config": {
      "tag": "new_lead"
    }
  },
  "steps": [
    {
      "id": "step_1",
      "type": "send_sms",
      "config": {
        "body": "Hi {{first_name}}, thanks for your interest!"
      },
      "next": "step_2"
    },
    {
      "id": "step_2",
      "type": "delay",
      "config": {
        "duration": 86400
      },
      "next": "step_3"
    }
  ]
}
```

## Database Models

```python
# Add to backend/app/models/workflow.py

class WorkflowExecution(Base):
    """Individual step execution log."""
    __tablename__ = "workflow_executions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    enrollment_id = Column(UUID(as_uuid=True), ForeignKey("workflow_enrollments.id"))
    step_id = Column(String(100), nullable=False)
    step_type = Column(String(50), nullable=False)
    
    status = Column(String(20), default="pending")  # pending, running, completed, failed
    input_data = Column(JSONB, default={})
    output_data = Column(JSONB, default={})
    error_message = Column(Text)
    
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    
    __table_args__ = (
        Index("ix_executions_enrollment", "enrollment_id"),
    )
```

## Core Engine Implementation

```python
# backend/app/services/workflow/engine.py

from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import asyncio
from app.models import Workflow, WorkflowEnrollment, Contact
from app.services.workflow.actions import ActionRegistry

class WorkflowEngine:
    def __init__(self, db_session):
        self.db = db_session
        self.actions = ActionRegistry()
    
    async def execute_enrollment(self, enrollment: WorkflowEnrollment) -> None:
        """Execute workflow for an enrolled contact."""
        workflow = await self.get_workflow(enrollment.workflow_id)
        contact = await self.get_contact(enrollment.contact_id)
        
        definition = workflow.definition
        current_step = enrollment.current_step or definition["steps"][0]["id"]
        
        while current_step:
            step = self.get_step(definition, current_step)
            if not step:
                break
            
            # Execute the step
            result = await self.execute_step(step, contact, enrollment)
            
            # Log execution
            await self.log_execution(enrollment.id, step, result)
            
            # Determine next step
            if step["type"] == "condition":
                current_step = self.evaluate_condition(step, result)
            elif step["type"] == "delay":
                # Schedule for later
                await self.schedule_delay(enrollment, step)
                return
            else:
                current_step = step.get("next")
            
            # Update enrollment state
            enrollment.current_step = current_step
            enrollment.state = result.get("state", {})
        
        # Workflow completed
        enrollment.status = "completed"
        enrollment.completed_at = datetime.utcnow()
    
    async def execute_step(
        self, 
        step: Dict, 
        contact: Contact, 
        enrollment: WorkflowEnrollment
    ) -> Dict[str, Any]:
        """Execute a single workflow step."""
        action = self.actions.get(step["type"])
        if not action:
            raise ValueError(f"Unknown action type: {step['type']}")
        
        config = self.interpolate_config(step.get("config", {}), contact)
        return await action.execute(contact, config, enrollment.state)
    
    def interpolate_config(self, config: Dict, contact: Contact) -> Dict:
        """Replace {{tokens}} with contact data."""
        result = {}
        for key, value in config.items():
            if isinstance(value, str):
                result[key] = self.replace_tokens(value, contact)
            else:
                result[key] = value
        return result
    
    def replace_tokens(self, text: str, contact: Contact) -> str:
        """Replace tokens in text."""
        replacements = {
            "{{first_name}}": contact.first_name or "",
            "{{last_name}}": contact.last_name or "",
            "{{email}}": contact.email or "",
            "{{phone}}": contact.phone or "",
        }
        for token, value in replacements.items():
            text = text.replace(token, value)
        return text
```

## Action Interface

```python
# backend/app/services/workflow/actions/base.py

from abc import ABC, abstractmethod
from typing import Dict, Any
from app.models import Contact

class WorkflowAction(ABC):
    """Base class for all workflow actions."""
    
    @property
    @abstractmethod
    def action_type(self) -> str:
        """Unique identifier for this action."""
        pass
    
    @abstractmethod
    async def execute(
        self, 
        contact: Contact, 
        config: Dict[str, Any],
        state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute the action.
        
        Returns:
            Dict with:
            - success: bool
            - state: updated state dict
            - output: any output data
            - error: error message if failed
        """
        pass
    
    def validate_config(self, config: Dict) -> bool:
        """Validate action configuration."""
        return True

class ActionRegistry:
    """Registry of available actions."""
    
    def __init__(self):
        self._actions: Dict[str, WorkflowAction] = {}
    
    def register(self, action: WorkflowAction):
        self._actions[action.action_type] = action
    
    def get(self, action_type: str) -> Optional[WorkflowAction]:
        return self._actions.get(action_type)
```

## Built-in Actions

```python
# backend/app/services/workflow/actions/messaging.py

class SendSMSAction(WorkflowAction):
    action_type = "send_sms"
    
    async def execute(self, contact, config, state):
        from app.services.sms import SMSService
        
        body = config.get("body") or config.get("template")
        
        sms_service = SMSService()
        result = await sms_service.send(
            to=contact.phone,
            body=body
        )
        
        return {
            "success": result.get("success", False),
            "output": {"message_id": result.get("sid")},
            "state": state
        }

class SendEmailAction(WorkflowAction):
    action_type = "send_email"
    
    async def execute(self, contact, config, state):
        from app.services.email import EmailService
        
        email_service = EmailService()
        result = await email_service.send_template(
            template_id=config.get("template"),
            to=contact.email,
            data={"contact": contact}
        )
        
        return {"success": True, "output": result, "state": state}
```

```python
# backend/app/services/workflow/actions/crm.py

class AddTagAction(WorkflowAction):
    action_type = "add_tag"
    
    async def execute(self, contact, config, state):
        tag = config.get("tag")
        if tag and tag not in contact.tags:
            contact.tags = contact.tags + [tag]
        return {"success": True, "state": state}

class RemoveTagAction(WorkflowAction):
    action_type = "remove_tag"
    
    async def execute(self, contact, config, state):
        tag = config.get("tag")
        if tag in contact.tags:
            contact.tags = [t for t in contact.tags if t != tag]
        return {"success": True, "state": state}

class UpdateFieldAction(WorkflowAction):
    action_type = "update_field"
    
    async def execute(self, contact, config, state):
        field = config.get("field")
        value = config.get("value")
        
        if hasattr(contact, field):
            setattr(contact, field, value)
        else:
            contact.custom_fields[field] = value
        
        return {"success": True, "state": state}
```

```python
# backend/app/services/workflow/actions/logic.py

class DelayAction(WorkflowAction):
    action_type = "delay"
    
    async def execute(self, contact, config, state):
        duration = config.get("duration", 1)
        unit = config.get("unit", "days")
        
        # Calculate next execution time
        if unit == "minutes":
            delta = timedelta(minutes=duration)
        elif unit == "hours":
            delta = timedelta(hours=duration)
        elif unit == "days":
            delta = timedelta(days=duration)
        
        return {
            "success": True,
            "state": state,
            "delay_until": datetime.utcnow() + delta
        }

class ConditionAction(WorkflowAction):
    action_type = "condition"
    
    async def execute(self, contact, config, state):
        field = config.get("field")
        operator = config.get("operator")
        value = config.get("value")
        
        # Get field value
        actual = getattr(contact, field, None)
        if actual is None:
            actual = contact.custom_fields.get(field)
        
        # Evaluate condition
        result = self.evaluate(actual, operator, value)
        
        return {
            "success": True,
            "state": state,
            "condition_result": result
        }
    
    def evaluate(self, actual, operator, expected) -> bool:
        if operator == "equals":
            return actual == expected
        elif operator == "not_equals":
            return actual != expected
        elif operator == "contains":
            return expected in (actual or "")
        elif operator == "exists":
            return actual is not None
        elif operator == "greater_than":
            return (actual or 0) > expected
        elif operator == "less_than":
            return (actual or 0) < expected
        return False

class ABSplitAction(WorkflowAction):
    action_type = "ab_split"
    
    async def execute(self, contact, config, state):
        import random
        
        paths = config.get("paths", ["a", "b"])
        weights = config.get("weights", [50, 50])
        
        # Weighted random selection
        selected = random.choices(paths, weights=weights)[0]
        
        return {
            "success": True,
            "state": state,
            "selected_path": selected
        }
```

## Trigger System

```python
# backend/app/services/workflow/triggers.py

from typing import List
from app.models import Workflow, Contact

class TriggerRegistry:
    """Manages workflow triggers."""
    
    async def check_contact_created(self, contact: Contact) -> List[Workflow]:
        """Find workflows triggered by contact creation."""
        # Query workflows with trigger_type = "contact_created"
        # Filter by conditions (e.g., source = "facebook_ad")
        pass
    
    async def check_tag_added(self, contact: Contact, tag: str) -> List[Workflow]:
        """Find workflows triggered by tag addition."""
        pass
    
    async def check_sms_received(self, contact: Contact, message: str) -> List[Workflow]:
        """Find workflows triggered by incoming SMS."""
        pass
    
    async def check_field_updated(
        self, 
        contact: Contact, 
        field: str, 
        old_value, 
        new_value
    ) -> List[Workflow]:
        """Find workflows triggered by field changes."""
        pass
```

## Background Worker

```python
# backend/app/workers/workflow_worker.py

import asyncio
from datetime import datetime
from app.core.database import AsyncSessionLocal
from app.services.workflow.engine import WorkflowEngine
from app.models import WorkflowEnrollment

async def process_scheduled_steps():
    """Process workflow steps that are due."""
    async with AsyncSessionLocal() as db:
        # Find enrollments with next_action_at <= now
        query = select(WorkflowEnrollment).where(
            WorkflowEnrollment.status == "active",
            WorkflowEnrollment.next_action_at <= datetime.utcnow()
        )
        result = await db.execute(query)
        enrollments = result.scalars().all()
        
        engine = WorkflowEngine(db)
        
        for enrollment in enrollments:
            try:
                await engine.execute_enrollment(enrollment)
            except Exception as e:
                enrollment.status = "failed"
                # Log error
        
        await db.commit()

async def run_worker():
    """Run the workflow worker loop."""
    while True:
        await process_scheduled_steps()
        await asyncio.sleep(10)  # Check every 10 seconds
```

## API Endpoints

```python
# Add to backend/app/api/routes/workflows.py

@router.post("/{workflow_id}/import")
async def import_workflow_definition(
    workflow_id: UUID,
    definition: dict,
    db: AsyncSession = Depends(get_db)
):
    """Import YAML/JSON workflow definition."""
    # Validate definition schema
    # Parse and store
    pass

@router.get("/{workflow_id}/export")
async def export_workflow_definition(
    workflow_id: UUID,
    format: str = "json",
    db: AsyncSession = Depends(get_db)
):
    """Export workflow as YAML or JSON."""
    pass

@router.post("/{workflow_id}/test")
async def test_workflow(
    workflow_id: UUID,
    contact_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Dry-run workflow with a test contact."""
    pass

@router.get("/{workflow_id}/enrollments")
async def list_enrollments(
    workflow_id: UUID,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """List contacts enrolled in workflow."""
    pass
```

## Success Criteria

- [ ] Parse YAML workflow definitions
- [ ] Parse JSON workflow definitions
- [ ] Execute linear workflows (A → B → C)
- [ ] Execute conditional branches
- [ ] Handle delays/scheduling
- [ ] SMS action working
- [ ] Email action working
- [ ] Tag add/remove actions
- [ ] Field update actions
- [ ] A/B split action
- [ ] Background worker processing
- [ ] Trigger: contact_created
- [ ] Trigger: tag_added
- [ ] Trigger: sms_received
- [ ] API for import/export
- [ ] 15+ unit tests
