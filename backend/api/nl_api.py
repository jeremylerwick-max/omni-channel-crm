"""
Natural Language API endpoint for CRM control.

Enables users to control CRM with plain English commands.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import logging

from modules.natural_language_interface.crm_recognizer import CRMIntentRecognizer
from modules.natural_language_interface.crm_executor import CRMCommandExecutor

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/nl", tags=["Natural Language"])

# Initialize recognizer (shared across requests)
recognizer = CRMIntentRecognizer(use_llm_fallback=True)


class NLRequest(BaseModel):
    """Natural language request."""
    text: str = Field(..., description="Natural language command", example="Show me leads from today")
    location_id: str = Field(
        default="00000000-0000-0000-0000-000000000001",
        description="Location ID for CRM operations"
    )


class NLResponse(BaseModel):
    """Natural language response."""
    success: bool
    intent: str
    confidence: float
    result: Dict[str, Any]
    raw_command: Optional[Dict[str, Any]] = None


@router.post("/command", response_model=NLResponse)
async def execute_nl_command(request: NLRequest):
    """
    Execute a natural language CRM command.

    **Examples:**
    - "Show me leads from today"
    - "Find contacts tagged 'hot lead'"
    - "Text John Smith saying 'Hey, following up!'"
    - "Schedule a call with Jane tomorrow at 2pm"
    - "How many contacts do I have?"

    **Returns:**
    - success: Whether command executed successfully
    - intent: Recognized intent (e.g., "search_contacts")
    - confidence: Confidence score (0-1)
    - result: Command execution results
    - raw_command: Parsed command details
    """
    try:
        # Parse command
        command = recognizer.recognize(request.text)

        logger.info(
            f"NL Command: '{request.text}' -> Intent: {command.intent.value} "
            f"(confidence: {command.confidence:.2f})"
        )

        # Execute
        executor = CRMCommandExecutor(location_id=request.location_id)
        result = await executor.execute(command)

        return NLResponse(
            success=result.get("success", False),
            intent=command.intent.value,
            confidence=command.confidence,
            result=result,
            raw_command={
                "intent": command.intent.value,
                "entities": [e.dict() for e in command.entities],
                "confidence": command.confidence
            }
        )

    except Exception as e:
        logger.exception(f"Error executing NL command: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/parse")
async def parse_only(request: NLRequest):
    """
    Parse natural language without executing.

    Useful for debugging and testing intent recognition.

    **Examples:**
    - "show me leads from today"
    - "text 949-230-0036 saying hello"
    - "schedule call with John tomorrow at 2pm"

    **Returns:**
    - intent: Recognized intent
    - entities: Extracted entities (phone, email, date, time, tag, name)
    - confidence: Recognition confidence score
    - raw_input: Original input text
    """
    try:
        command = recognizer.recognize(request.text)

        return {
            "intent": command.intent.value,
            "entities": [e.dict() for e in command.entities],
            "confidence": command.confidence,
            "raw_input": command.raw_input
        }

    except Exception as e:
        logger.exception(f"Error parsing NL command: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/intents")
async def list_intents():
    """
    List all supported intents.

    **Returns:**
    List of supported CRM intents with descriptions and example phrases.
    """
    from modules.natural_language_interface.crm_intents import INTENT_PATTERNS

    intents = []
    for intent, patterns in INTENT_PATTERNS.items():
        intents.append({
            "intent": intent.value,
            "description": intent.value.replace("_", " ").title(),
            "example_phrases": patterns[:3],  # First 3 patterns
        })

    return {
        "intents": intents,
        "count": len(intents)
    }
