"""
Intent recognition for CRM commands.

Uses keyword matching first, falls back to LLM for ambiguous cases.
"""

import re
import logging
from typing import Optional, List, Tuple, Any
from datetime import datetime, timedelta

from .crm_intents import (
    CRMIntent, CRMEntity, CRMCommand,
    INTENT_PATTERNS, ENTITY_PATTERNS
)

logger = logging.getLogger(__name__)


class CRMIntentRecognizer:
    """Recognizes CRM intents from natural language input."""

    def __init__(self, use_llm_fallback: bool = True):
        self.use_llm_fallback = use_llm_fallback

    def recognize(self, text: str) -> CRMCommand:
        """
        Parse natural language input into a CRM command.

        Args:
            text: User's natural language input

        Returns:
            CRMCommand with intent, entities, and confidence
        """
        text_lower = text.lower().strip()

        # Step 1: Try keyword matching (fast)
        intent, confidence = self._match_intent(text_lower)

        # Step 2: Extract entities
        entities = self._extract_entities(text)

        # Step 3: If low confidence and LLM enabled, use LLM
        if confidence < 0.6 and self.use_llm_fallback:
            intent, confidence, extra_entities = self._llm_recognize(text)
            entities.extend(extra_entities)

        return CRMCommand(
            intent=intent,
            entities=entities,
            raw_input=text,
            confidence=confidence
        )

    def _match_intent(self, text: str) -> Tuple[CRMIntent, float]:
        """Match intent using keyword patterns."""
        best_intent = CRMIntent.UNKNOWN
        best_score = 0.0

        for intent, patterns in INTENT_PATTERNS.items():
            for pattern in patterns:
                if pattern in text:
                    # Score based on pattern length (longer = more specific)
                    score = len(pattern) / len(text) if text else 0
                    score = min(score * 2, 0.95)  # Cap at 0.95

                    if score > best_score:
                        best_score = score
                        best_intent = intent

        return best_intent, best_score

    def _extract_entities(self, text: str) -> List[CRMEntity]:
        """Extract entities using regex patterns."""
        entities = []

        for entity_type, pattern in ENTITY_PATTERNS.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                # Handle tuple results from groups
                value = match if isinstance(match, str) else next((m for m in match if m), None)
                if value:
                    entities.append(CRMEntity(
                        entity_type=entity_type,
                        value=self._normalize_entity(entity_type, value)
                    ))

        # Extract names (simple heuristic: capitalized words not at start)
        words = text.split()
        for i, word in enumerate(words):
            if i > 0 and word and word[0].isupper() and word.isalpha():
                entities.append(CRMEntity(
                    entity_type="name",
                    value=word,
                    confidence=0.7
                ))

        return entities

    def _normalize_entity(self, entity_type: str, value: str) -> Any:
        """Normalize extracted entity values."""
        if entity_type == "date_relative":
            return self._parse_relative_date(value.lower())
        elif entity_type == "phone":
            # Strip to digits only
            digits = re.sub(r'\D', '', value)
            if len(digits) == 10:
                return f"+1{digits}"
            elif len(digits) == 11 and digits[0] == '1':
                return f"+{digits}"
            return value
        return value

    def _parse_relative_date(self, text: str) -> str:
        """Convert relative date to ISO format."""
        today = datetime.now().date()

        if text == "today":
            return today.isoformat()
        elif text == "tomorrow":
            return (today + timedelta(days=1)).isoformat()
        elif text == "yesterday":
            return (today - timedelta(days=1)).isoformat()
        elif text == "this week":
            # Start of this week (Monday)
            start = today - timedelta(days=today.weekday())
            return start.isoformat()
        elif text == "last week":
            start = today - timedelta(days=today.weekday() + 7)
            return start.isoformat()
        elif text == "next week":
            start = today + timedelta(days=(7 - today.weekday()))
            return start.isoformat()

        return text

    def _llm_recognize(self, text: str) -> Tuple[CRMIntent, float, List[CRMEntity]]:
        """Use LLM for ambiguous intent recognition (placeholder)."""
        # TODO: Implement LLM fallback using Claude Haiku
        # For now, return unknown with low confidence
        return CRMIntent.UNKNOWN, 0.3, []
