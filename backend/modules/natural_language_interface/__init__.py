"""
Natural Language Interface Module

Convert natural language commands into structured CRM operations.
Features:
- CRM intent recognition (search, send SMS, create appointments, stats)
- Entity extraction (phone, email, date, time, tags, names)
- Command execution with confidence scoring
- Keyword matching with LLM fallback
"""

from .crm_intents import CRMIntent, CRMEntity, CRMCommand, INTENT_PATTERNS, ENTITY_PATTERNS
from .crm_recognizer import CRMIntentRecognizer
from .crm_executor import CRMCommandExecutor

__all__ = [
    'CRMIntent',
    'CRMEntity',
    'CRMCommand',
    'INTENT_PATTERNS',
    'ENTITY_PATTERNS',
    'CRMIntentRecognizer',
    'CRMCommandExecutor'
]
