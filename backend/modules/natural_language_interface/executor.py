"""
Natural Language Interface Executor

Integrates intent recognition, entity extraction, slot filling,
and conversation management to process natural language commands.
"""

import sys
import json
import logging
from typing import Dict, Any

from .intent_recognizer import IntentRecognizer
from .entity_extractor import EntityExtractor
from .slot_filler import SlotFiller
from .conversation_manager import ConversationManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global instances
INTENT_RECOGNIZER = None
ENTITY_EXTRACTOR = None
SLOT_FILLER = None
CONVERSATION_MANAGER = None


def initialize():
    """Initialize NLI components."""
    global INTENT_RECOGNIZER, ENTITY_EXTRACTOR, SLOT_FILLER, CONVERSATION_MANAGER

    if INTENT_RECOGNIZER is None:
        INTENT_RECOGNIZER = IntentRecognizer()
        ENTITY_EXTRACTOR = EntityExtractor()
        SLOT_FILLER = SlotFiller()
        CONVERSATION_MANAGER = ConversationManager()
        logger.info("Natural Language Interface initialized")


def execute(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Execute NLI action.

    Args:
        inputs: Dict with 'action' and action-specific parameters

    Returns:
        Dict with 'success', 'action', 'result'/'error'
    """
    try:
        initialize()
        action = inputs.get('action')

        if action == 'parse':
            result = _parse(inputs)
        elif action == 'recognize_intent':
            result = _recognize_intent(inputs)
        elif action == 'extract_entities':
            result = _extract_entities(inputs)
        elif action == 'fill_slots':
            result = _fill_slots(inputs)
        elif action == 'create_conversation':
            result = _create_conversation(inputs)
        elif action == 'add_turn':
            result = _add_turn(inputs)
        elif action == 'get_context':
            result = _get_context(inputs)
        elif action == 'get_history':
            result = _get_history(inputs)
        elif action == 'suggest_modules':
            result = _suggest_modules(inputs)
        else:
            return {
                'success': False,
                'action': action,
                'error': f'Unknown action: {action}'
            }

        return {
            'success': True,
            'action': action,
            'result': result
        }

    except Exception as e:
        logger.error(f"Error executing {action}: {e}", exc_info=True)
        return {
            'success': False,
            'action': inputs.get('action', 'unknown'),
            'error': str(e)
        }


def _parse(inputs: Dict) -> Dict:
    """Fully parse natural language input.

    Args:
        inputs: Dict with 'text' and optional 'conv_id'

    Returns:
        Complete NLI analysis
    """
    text = inputs['text']
    conv_id = inputs.get('conv_id')

    # Get context if conversation exists
    context = None
    if conv_id:
        context = CONVERSATION_MANAGER.get_context(conv_id)

    # Recognize intent
    if context:
        intent_result = INTENT_RECOGNIZER.recognize_with_context(text, context)
    else:
        intent_result = INTENT_RECOGNIZER.recognize(text)

    # Extract entities
    entities = ENTITY_EXTRACTOR.extract(text)

    # Fill slots (need module params - stub for now)
    module_params = inputs.get('module_params', {})
    filled_slots = SLOT_FILLER.fill_slots(entities, module_params, intent_result['intent'])

    return {
        "text": text,
        "intent": intent_result,
        "entities": entities,
        "filled_slots": filled_slots,
        "conv_id": conv_id
    }


def _recognize_intent(inputs: Dict) -> Dict:
    """Recognize intent from text."""
    text = inputs['text']
    context = inputs.get('context')

    if context:
        return INTENT_RECOGNIZER.recognize_with_context(text, context)
    return INTENT_RECOGNIZER.recognize(text)


def _extract_entities(inputs: Dict) -> Dict:
    """Extract entities from text."""
    text = inputs['text']
    return ENTITY_EXTRACTOR.extract(text)


def _fill_slots(inputs: Dict) -> Dict:
    """Fill parameter slots."""
    return SLOT_FILLER.fill_slots(
        entities=inputs['entities'],
        module_params=inputs['module_params'],
        intent=inputs['intent']
    )


def _create_conversation(inputs: Dict) -> str:
    """Create new conversation."""
    user_id = inputs.get('user_id')
    conv_id = CONVERSATION_MANAGER.create_conversation(user_id)
    return {"conversation_id": conv_id}


def _add_turn(inputs: Dict) -> Dict:
    """Add conversation turn."""
    CONVERSATION_MANAGER.add_turn(
        conv_id=inputs['conversation_id'],
        user_input=inputs['user_input'],
        intent=inputs['intent'],
        entities=inputs.get('entities', {}),
        response=inputs.get('response', {})
    )
    return {"added": True}


def _get_context(inputs: Dict) -> Dict:
    """Get conversation context."""
    conv_id = inputs['conversation_id']
    return CONVERSATION_MANAGER.get_context(conv_id)


def _get_history(inputs: Dict) -> List:
    """Get conversation history."""
    conv_id = inputs['conversation_id']
    last_n = inputs.get('last_n')
    return CONVERSATION_MANAGER.get_history(conv_id, last_n)


def _suggest_modules(inputs: Dict) -> List:
    """Suggest modules based on text."""
    text = inputs['text']
    return INTENT_RECOGNIZER.suggest_modules(text)


def main():
    """Main entry point."""
    if len(sys.argv) > 1:
        inputs = json.loads(sys.argv[1])
    else:
        inputs = json.load(sys.stdin)

    result = execute(inputs)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
