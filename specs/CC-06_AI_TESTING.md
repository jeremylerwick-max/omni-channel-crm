# CC-06: AI Workflow Testing Layer

## Overview
**THE KILLER FEATURE** - LLM-powered workflow validation that no competitor has. Simulate leads through campaigns before launch.

## Repository
`/Users/mac/Desktop/omni-channel-crm`

## Priority
**P0 - Differentiator** - This is what makes us different from GoHighLevel.

## Concept

The AI Testing Layer allows users to:
1. Create virtual "test personas" (AI-simulated leads)
2. Run workflows in simulation mode
3. Have the AI respond to messages as a real lead would
4. Validate that logic branches correctly
5. Get a test report before going live

## Files to Create

```
backend/app/services/ai_testing/
├── __init__.py
├── simulator.py        # Main simulation engine
├── personas.py         # AI persona management
├── validator.py        # Logic validation
├── reporter.py         # Test report generation
└── providers/
    ├── __init__.py
    ├── anthropic.py    # Claude implementation
    ├── openai.py       # GPT implementation
    └── ollama.py       # Local LLM
```

## Database Schema

```sql
CREATE TABLE test_personas (
    id UUID PRIMARY KEY,
    account_id UUID REFERENCES accounts(id),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    personality JSONB DEFAULT '{}',
    demographics JSONB DEFAULT '{}',
    behavior_traits JSONB DEFAULT '[]',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE workflow_tests (
    id UUID PRIMARY KEY,
    workflow_id UUID REFERENCES workflows(id),
    persona_id UUID REFERENCES test_personas(id),
    status VARCHAR(20) DEFAULT 'pending',
    config JSONB DEFAULT '{}',
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE test_interactions (
    id UUID PRIMARY KEY,
    test_id UUID REFERENCES workflow_tests(id),
    step_id VARCHAR(100),
    step_type VARCHAR(50),
    message_sent TEXT,
    ai_response TEXT,
    ai_reasoning TEXT,
    expected_outcome VARCHAR(100),
    actual_outcome VARCHAR(100),
    passed BOOLEAN,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE test_reports (
    id UUID PRIMARY KEY,
    test_id UUID REFERENCES workflow_tests(id),
    summary TEXT,
    issues JSONB DEFAULT '[]',
    recommendations JSONB DEFAULT '[]',
    score INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

## Persona Definition

```json
{
  "name": "Skeptical Sarah",
  "description": "A busy professional who needs convincing",
  "personality": {
    "tone": "skeptical",
    "response_length": "short",
    "decision_speed": "slow",
    "objection_likelihood": "high"
  },
  "demographics": {
    "age_range": "35-45",
    "occupation": "Marketing Manager",
    "location": "Urban",
    "income": "High"
  },
  "behavior_traits": [
    "asks_questions_before_buying",
    "compares_competitors",
    "values_reviews",
    "responds_slowly"
  ]
}
```

## Simulation Engine

```python
# backend/app/services/ai_testing/simulator.py

from typing import Dict, Any, List, Optional
from app.models import Workflow, Contact
from app.services.ai_testing.personas import PersonaManager
from app.services.ai_testing.providers import AIProvider

class WorkflowSimulator:
    def __init__(self, ai_provider: AIProvider):
        self.ai = ai_provider
        self.persona_manager = PersonaManager()
    
    async def run_simulation(
        self,
        workflow: Workflow,
        persona_id: str,
        max_steps: int = 50
    ) -> Dict[str, Any]:
        """
        Run a complete workflow simulation with an AI persona.
        """
        persona = await self.persona_manager.get(persona_id)
        
        # Create virtual contact based on persona
        virtual_contact = self.create_virtual_contact(persona)
        
        # Initialize simulation state
        sim_state = {
            "persona": persona,
            "contact": virtual_contact,
            "step_count": 0,
            "interactions": [],
            "current_step": None,
            "completed": False
        }
        
        # Execute workflow steps
        definition = workflow.definition
        current_step_id = definition["steps"][0]["id"]
        
        while current_step_id and sim_state["step_count"] < max_steps:
            step = self.get_step(definition, current_step_id)
            if not step:
                break
            
            sim_state["current_step"] = step
            sim_state["step_count"] += 1
            
            # Execute and record interaction
            interaction = await self.execute_simulated_step(step, sim_state)
            sim_state["interactions"].append(interaction)
            
            # Determine next step based on AI response
            current_step_id = await self.determine_next_step(
                step, interaction, definition
            )
        
        sim_state["completed"] = True
        return sim_state
    
    async def execute_simulated_step(
        self,
        step: Dict,
        sim_state: Dict
    ) -> Dict[str, Any]:
        """Execute a step and get AI persona response."""
        
        interaction = {
            "step_id": step["id"],
            "step_type": step["type"],
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if step["type"] == "send_sms":
            # Generate the message that would be sent
            message = self.render_message(
                step["config"].get("body", ""),
                sim_state["contact"]
            )
            interaction["message_sent"] = message
            
            # Get AI response as if they received this SMS
            ai_response = await self.get_persona_response(
                sim_state["persona"],
                "sms",
                message,
                sim_state["interactions"]
            )
            interaction["ai_response"] = ai_response["response"]
            interaction["ai_reasoning"] = ai_response["reasoning"]
            
        elif step["type"] == "send_email":
            subject = step["config"].get("subject", "")
            body = step["config"].get("body", "")
            interaction["message_sent"] = f"Subject: {subject}\n\n{body}"
            
            ai_response = await self.get_persona_response(
                sim_state["persona"],
                "email",
                interaction["message_sent"],
                sim_state["interactions"]
            )
            interaction["ai_response"] = ai_response["response"]
            interaction["ai_reasoning"] = ai_response["reasoning"]
            
        elif step["type"] == "condition":
            # Evaluate condition based on simulated state
            interaction["condition_evaluated"] = True
            
        elif step["type"] == "delay":
            interaction["delay_simulated"] = True
            interaction["delay_duration"] = step["config"]
        
        return interaction
    
    async def get_persona_response(
        self,
        persona: Dict,
        channel: str,
        message: str,
        history: List[Dict]
    ) -> Dict[str, str]:
        """Get AI-generated response as the persona."""
        
        prompt = f"""You are simulating a lead/customer receiving marketing messages.

PERSONA:
- Name: {persona['name']}
- Description: {persona['description']}
- Personality: {persona['personality']}
- Behavior: {persona['behavior_traits']}

CHANNEL: {channel}

MESSAGE RECEIVED:
{message}

CONVERSATION HISTORY:
{self.format_history(history)}

Based on this persona's characteristics, generate:
1. A realistic response this person would send (or "NO_RESPONSE" if they wouldn't reply)
2. Your reasoning for this response

Respond in JSON format:
{{
  "response": "the message they would send or NO_RESPONSE",
  "reasoning": "why they would respond this way",
  "sentiment": "positive/negative/neutral",
  "likely_to_convert": 0-100
}}
"""
        
        result = await self.ai.complete(prompt)
        return json.loads(result)
```

## Validation Engine

```python
# backend/app/services/ai_testing/validator.py

class WorkflowValidator:
    """Validates workflow logic and message quality."""
    
    async def validate_workflow(self, workflow: Workflow) -> Dict[str, Any]:
        """Run all validations on a workflow."""
        issues = []
        
        # Structural validation
        issues.extend(self.validate_structure(workflow.definition))
        
        # Message quality validation
        issues.extend(await self.validate_messages(workflow.definition))
        
        # Logic validation
        issues.extend(self.validate_logic(workflow.definition))
        
        return {
            "valid": len([i for i in issues if i["severity"] == "error"]) == 0,
            "issues": issues,
            "score": self.calculate_score(issues)
        }
    
    def validate_structure(self, definition: Dict) -> List[Dict]:
        """Check workflow structure is valid."""
        issues = []
        
        # Check for orphan steps (unreachable)
        reachable = self.find_reachable_steps(definition)
        all_steps = {s["id"] for s in definition.get("steps", [])}
        orphans = all_steps - reachable
        
        for orphan in orphans:
            issues.append({
                "severity": "warning",
                "type": "orphan_step",
                "step_id": orphan,
                "message": f"Step '{orphan}' is not reachable from any path"
            })
        
        # Check for infinite loops
        if self.has_infinite_loop(definition):
            issues.append({
                "severity": "error",
                "type": "infinite_loop",
                "message": "Workflow contains an infinite loop without exit condition"
            })
        
        return issues
    
    async def validate_messages(self, definition: Dict) -> List[Dict]:
        """Use AI to validate message quality."""
        issues = []
        
        for step in definition.get("steps", []):
            if step["type"] in ["send_sms", "send_email"]:
                body = step.get("config", {}).get("body", "")
                
                # AI analysis of message
                analysis = await self.analyze_message(body, step["type"])
                
                if analysis.get("spam_score", 0) > 70:
                    issues.append({
                        "severity": "warning",
                        "type": "spam_risk",
                        "step_id": step["id"],
                        "message": f"Message may trigger spam filters: {analysis['reason']}"
                    })
                
                if analysis.get("sentiment") == "aggressive":
                    issues.append({
                        "severity": "warning",
                        "type": "tone_issue",
                        "step_id": step["id"],
                        "message": "Message tone may be too aggressive"
                    })
        
        return issues
```

## Report Generator

```python
# backend/app/services/ai_testing/reporter.py

class TestReporter:
    """Generates human-readable test reports."""
    
    async def generate_report(
        self,
        simulation: Dict,
        validation: Dict
    ) -> Dict[str, Any]:
        """Generate comprehensive test report."""
        
        report = {
            "summary": self.generate_summary(simulation, validation),
            "score": self.calculate_overall_score(simulation, validation),
            "interactions": self.format_interactions(simulation["interactions"]),
            "issues": validation["issues"],
            "recommendations": await self.generate_recommendations(
                simulation, validation
            ),
            "conversion_likelihood": self.estimate_conversion(simulation)
        }
        
        return report
    
    async def generate_recommendations(
        self,
        simulation: Dict,
        validation: Dict
    ) -> List[str]:
        """AI-generated recommendations for improvement."""
        
        prompt = f"""Based on this workflow test:

SIMULATION RESULTS:
{json.dumps(simulation['interactions'], indent=2)}

VALIDATION ISSUES:
{json.dumps(validation['issues'], indent=2)}

Provide 3-5 specific, actionable recommendations to improve this workflow.
Focus on:
1. Message timing and frequency
2. Message content and tone
3. Logic and branching
4. Conversion optimization

Return as JSON array of strings.
"""
        
        result = await self.ai.complete(prompt)
        return json.loads(result)
```

## API Endpoints

```python
# backend/app/api/routes/ai_testing.py

router = APIRouter(prefix="/ai-testing", tags=["AI Testing"])

@router.get("/personas")
async def list_personas(db: AsyncSession = Depends(get_db)):
    """List available test personas."""
    pass

@router.post("/personas")
async def create_persona(data: PersonaCreate, db: AsyncSession = Depends(get_db)):
    """Create a custom test persona."""
    pass

@router.post("/workflows/{workflow_id}/test")
async def run_workflow_test(
    workflow_id: UUID,
    persona_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Run AI simulation test on a workflow."""
    simulator = WorkflowSimulator(get_ai_provider())
    workflow = await get_workflow(workflow_id)
    
    result = await simulator.run_simulation(workflow, str(persona_id))
    
    # Store test results
    # Generate report
    
    return result

@router.get("/tests/{test_id}")
async def get_test_result(test_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get results of a workflow test."""
    pass

@router.get("/tests/{test_id}/report")
async def get_test_report(test_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get detailed test report."""
    pass

@router.post("/workflows/{workflow_id}/validate")
async def validate_workflow(workflow_id: UUID, db: AsyncSession = Depends(get_db)):
    """Run validation checks on workflow."""
    validator = WorkflowValidator()
    workflow = await get_workflow(workflow_id)
    return await validator.validate_workflow(workflow)
```

## Default Personas

Include these built-in personas:

1. **Eager Eddie** - Quick to respond, ready to buy
2. **Skeptical Sarah** - Needs convincing, asks questions
3. **Busy Bob** - Rarely responds, short messages
4. **Chatty Cathy** - Long responses, asks many questions
5. **Cold Carl** - No interest, tests opt-out handling
6. **Price-Conscious Pam** - Always asks about cost
7. **Technical Tim** - Wants details and specs

## Success Criteria

- [ ] AI persona management (CRUD)
- [ ] Workflow simulation engine
- [ ] SMS response simulation
- [ ] Email response simulation
- [ ] Condition evaluation simulation
- [ ] Validation: structural checks
- [ ] Validation: message quality
- [ ] Validation: spam detection
- [ ] Test report generation
- [ ] AI recommendations
- [ ] 7 default personas
- [ ] Anthropic provider
- [ ] OpenAI provider
- [ ] Ollama provider
- [ ] API endpoints
- [ ] 12+ unit tests
