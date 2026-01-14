# CC-06: AI Workflow Testing Layer
## Claude Code Task Specification

**Module:** LLM-Powered Workflow Validation
**Priority:** P0 (MVP Critical - KILLER FEATURE)
**Estimated Time:** 3-4 days
**Dependencies:** CC-03 (Workflow Engine v2)

---

## Objective

Build an AI testing layer that simulates leads through workflows, validates logic, and catches issues before going live. **THIS IS OUR KEY DIFFERENTIATOR - GHL DOESN'T HAVE THIS.**

---

## Technical Requirements

### 1. Directory Structure
```
backend/modules/ai_testing/
├── __init__.py
├── simulator.py          # Lead simulation engine
├── personas.py           # AI persona definitions
├── validator.py          # Workflow validation
├── analyzer.py           # Message tone/intent analysis
├── reporter.py           # Test report generation
├── providers/
│   ├── __init__.py
│   ├── base.py           # Provider interface
│   ├── openai.py         # OpenAI GPT
│   ├── anthropic.py      # Claude
│   └── ollama.py         # Local Ollama
└── tests/
    ├── test_simulator.py
    ├── test_validator.py
    └── test_personas.py
```

### 2. Database Schema
```sql
-- backend/schema/023_ai_testing.sql

CREATE TABLE workflow_tests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id UUID REFERENCES workflows_v2(id),
    name VARCHAR(255),
    persona_config JSONB NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',  -- pending, running, completed, failed
    results JSONB,
    issues_found INT DEFAULT 0,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE test_simulations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    test_id UUID REFERENCES workflow_tests(id),
    step_id VARCHAR(100),
    step_type VARCHAR(50),
    message_sent TEXT,
    ai_response TEXT,
    ai_analysis JSONB,
    expected_outcome VARCHAR(100),
    actual_outcome VARCHAR(100),
    passed BOOLEAN,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### 3. Persona System
```python
# backend/modules/ai_testing/personas.py

class TestPersona(BaseModel):
    name: str
    description: str
    behavior: str  # "interested", "skeptical", "busy", "confused", "hostile"
    response_style: str  # "brief", "verbose", "professional", "casual"
    likelihood_to_convert: float  # 0.0 to 1.0
    objections: List[str]  # Common objections this persona might have
    custom_instructions: Optional[str]

BUILT_IN_PERSONAS = [
    TestPersona(
        name="Interested Prospect",
        description="Warm lead, ready to buy",
        behavior="interested",
        response_style="professional",
        likelihood_to_convert=0.8,
        objections=["What's the price?", "How long does it take?"]
    ),
    TestPersona(
        name="Skeptical Shopper",
        description="Needs convincing, asks tough questions",
        behavior="skeptical",
        response_style="brief",
        likelihood_to_convert=0.3,
        objections=["Why should I trust you?", "I've heard bad things"]
    ),
    TestPersona(
        name="Busy Executive",
        description="Short on time, needs quick answers",
        behavior="busy",
        response_style="brief",
        likelihood_to_convert=0.5,
        objections=["I don't have time", "Send me an email instead"]
    ),
    TestPersona(
        name="Confused Customer",
        description="Doesn't understand product, asks clarifying questions",
        behavior="confused",
        response_style="verbose",
        likelihood_to_convert=0.4,
        objections=["I don't understand", "Can you explain that again?"]
    ),
    TestPersona(
        name="Hostile Opt-Out",
        description="Not interested, wants to unsubscribe",
        behavior="hostile",
        response_style="brief",
        likelihood_to_convert=0.0,
        objections=["STOP", "Unsubscribe me", "How did you get my number?"]
    ),
]
```

### 4. Simulator Engine
```python
# backend/modules/ai_testing/simulator.py

class WorkflowSimulator:
    def __init__(self, provider: AIProvider):
        self.provider = provider
    
    async def run_test(
        self,
        workflow_id: str,
        personas: List[TestPersona],
        max_steps: int = 20
    ) -> TestResult:
        """
        Simulate workflow with AI personas.
        
        For each persona:
        1. Create fake contact
        2. Enroll in workflow
        3. For each step that sends a message:
           - Send message to AI persona
           - Get AI response
           - Feed response back to workflow
           - Check if workflow handles correctly
        4. Validate all outcomes
        """
        results = []
        for persona in personas:
            result = await self._simulate_persona(workflow_id, persona, max_steps)
            results.append(result)
        
        return self._aggregate_results(results)
    
    async def _simulate_persona(
        self,
        workflow_id: str,
        persona: TestPersona,
        max_steps: int
    ) -> PersonaResult:
        # Create simulation context
        context = SimulationContext(persona=persona)
        
        # Get workflow definition
        workflow = await get_workflow(workflow_id)
        
        # Start at trigger, walk through steps
        current_step = workflow.get_first_step()
        step_count = 0
        
        while current_step and step_count < max_steps:
            step_result = await self._execute_step(current_step, context)
            
            if step_result.type == 'message':
                # AI responds to message
                ai_response = await self._get_ai_response(
                    step_result.message,
                    persona,
                    context
                )
                context.add_response(ai_response)
                
                # Analyze response intent
                analysis = await self._analyze_response(ai_response)
                step_result.ai_analysis = analysis
            
            context.steps.append(step_result)
            current_step = self._get_next_step(workflow, current_step, context)
            step_count += 1
        
        return PersonaResult(
            persona=persona,
            steps=context.steps,
            completed=current_step is None,
            issues=self._find_issues(context)
        )
    
    async def _get_ai_response(
        self,
        message: str,
        persona: TestPersona,
        context: SimulationContext
    ) -> str:
        prompt = f"""You are simulating a lead/customer with the following profile:
Name: {persona.name}
Behavior: {persona.behavior}
Response Style: {persona.response_style}
Likelihood to Convert: {persona.likelihood_to_convert * 100}%
Common Objections: {', '.join(persona.objections)}

You just received this message:
"{message}"

Previous conversation:
{context.get_conversation_history()}

Respond as this persona would. Keep it realistic and authentic.
If the persona is "hostile" and wants to unsubscribe, say STOP.
If confused, ask clarifying questions.
If interested, show enthusiasm and ask next steps."""

        return await self.provider.complete(prompt)
```

### 5. Validator
```python
# backend/modules/ai_testing/validator.py

class WorkflowValidator:
    async def validate(self, test_result: TestResult) -> ValidationReport:
        issues = []
        
        # Check for structural issues
        issues.extend(self._check_dead_ends(test_result))
        issues.extend(self._check_infinite_loops(test_result))
        issues.extend(self._check_unreachable_steps(test_result))
        
        # Check for logic issues
        issues.extend(self._check_condition_coverage(test_result))
        issues.extend(self._check_opt_out_handling(test_result))
        
        # Check for content issues
        issues.extend(await self._check_message_quality(test_result))
        issues.extend(await self._check_brand_consistency(test_result))
        
        return ValidationReport(issues=issues, score=self._calculate_score(issues))
    
    async def _check_message_quality(self, result: TestResult) -> List[Issue]:
        """Use AI to check message quality"""
        issues = []
        for step in result.get_message_steps():
            analysis = await self.ai.analyze_message(step.message)
            if analysis.spam_score > 0.7:
                issues.append(Issue(
                    severity='warning',
                    step_id=step.id,
                    message=f"Message may be perceived as spammy: {analysis.reason}"
                ))
            if analysis.clarity_score < 0.5:
                issues.append(Issue(
                    severity='info',
                    step_id=step.id,
                    message=f"Message clarity could be improved: {analysis.suggestion}"
                ))
        return issues
```

### 6. API Endpoints
```
POST   /api/workflows/{id}/test           # Run AI test
GET    /api/workflows/{id}/tests          # List test runs
GET    /api/tests/{id}                    # Get test result
GET    /api/tests/{id}/simulations        # Get step-by-step details
POST   /api/ai-testing/personas           # Create custom persona
GET    /api/ai-testing/personas           # List personas (built-in + custom)
POST   /api/ai-testing/analyze-message    # Analyze single message
```

---

## Test Report Output

```json
{
  "test_id": "uuid",
  "workflow_id": "uuid",
  "status": "completed",
  "duration_seconds": 45,
  "personas_tested": 5,
  "overall_score": 85,
  "summary": {
    "passed": 4,
    "failed": 1,
    "issues_found": 3
  },
  "issues": [
    {
      "severity": "error",
      "step_id": "check_response",
      "message": "Hostile persona said STOP but workflow continued sending messages",
      "suggestion": "Add opt-out detection before this step"
    },
    {
      "severity": "warning", 
      "step_id": "promo_email",
      "message": "Email subject may trigger spam filters (95% spam score)",
      "suggestion": "Avoid ALL CAPS and excessive punctuation"
    }
  ],
  "persona_results": [
    {
      "persona": "Interested Prospect",
      "passed": true,
      "steps_executed": 8,
      "converted": true,
      "notes": "Workflow correctly identified positive intent and routed to sales"
    }
  ]
}
```

---

## Acceptance Criteria

1. ✅ Simulate workflow with multiple AI personas
2. ✅ AI responds realistically to messages
3. ✅ Detect opt-out failures (STOP not handled)
4. ✅ Detect dead-end branches
5. ✅ Detect infinite loops
6. ✅ Analyze message quality (spam score)
7. ✅ Generate comprehensive test report
8. ✅ Support custom personas
9. ✅ Support OpenAI, Anthropic, Ollama
10. ✅ Test runs in < 60 seconds
11. ✅ 85%+ test coverage

---

## Marketing Value

**This feature alone justifies switching from GHL:**

- "Test your campaigns before going live"
- "AI-powered QA for your marketing funnels"
- "Catch opt-out compliance issues automatically"
- "Never send spammy messages again"
- "Simulate edge cases without real leads"
