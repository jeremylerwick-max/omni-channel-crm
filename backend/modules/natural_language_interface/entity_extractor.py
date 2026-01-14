"""
Entity Extractor

Extracts structured entities from natural language:
- URLs, emails, phone numbers
- Dates and times
- Numbers and quantities
- File paths
- Names and identifiers
"""

import re
import logging
from typing import Dict, List, Any
from datetime import datetime
from dateutil import parser as date_parser

logger = logging.getLogger(__name__)


class EntityExtractor:
    """Extract entities from natural language text."""

    def __init__(self):
        """Initialize entity extractor."""
        self.patterns = {
            "url": r'https?://[^\s]+',
            "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            "phone": r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
            "number": r'\b\d+(?:\.\d+)?\b',
            "file_path": r'(?:[A-Za-z]:|\.{1,2})?(?:/|\\)[^\s]+',
            "time": r'\b\d{1,2}:\d{2}(?::\d{2})?(?:\s*[AaPp][Mm])?\b'
        }
        logger.info("Entity Extractor initialized")

    def extract(self, text: str) -> Dict[str, List[Any]]:
        """Extract all entities from text.

        Args:
            text: Input text

        Returns:
            Dict mapping entity types to extracted values
        """
        try:
            entities = {}

            # Extract pattern-based entities
            for entity_type, pattern in self.patterns.items():
                matches = re.findall(pattern, text)
                if matches:
                    entities[entity_type] = matches

            # Extract dates (more complex)
            dates = self._extract_dates(text)
            if dates:
                entities["date"] = dates

            logger.info(f"Extracted {sum(len(v) for v in entities.values())} entities")
            return entities

        except Exception as e:
            logger.error(f"Error extracting entities: {e}")
            return {}

    def _extract_dates(self, text: str) -> List[str]:
        """Extract dates from text."""
        dates = []
        date_patterns = [
            r'\d{4}-\d{2}-\d{2}',
            r'\d{1,2}/\d{1,2}/\d{4}',
            r'\b(today|tomorrow|yesterday)\b'
        ]

        for pattern in date_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            dates.extend(matches)

        return dates


if __name__ == "__main__":
    extractor = EntityExtractor()
    text = "Navigate to https://example.com and email results to user@test.com by tomorrow at 2:30pm"
    entities = extractor.extract(text)
    print(f"Extracted: {entities}")
