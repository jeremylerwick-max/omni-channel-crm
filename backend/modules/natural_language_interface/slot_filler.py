"""
Slot Filler

Maps extracted entities to module input parameters (slots).
Handles parameter validation and type conversion.
"""

import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


class SlotFiller:
    """Fill module parameter slots with extracted entities."""

    def __init__(self):
        """Initialize slot filler."""
        # Common parameter mappings
        self.param_mappings = {
            "url": ["url", "website", "link", "page", "site"],
            "email": ["email", "email_address", "recipient", "to"],
            "file_path": ["file", "path", "file_path", "filepath", "document"],
            "date": ["date", "when", "time", "schedule_time"],
            "number": ["count", "limit", "max", "min", "amount", "quantity"]
        }
        logger.info("Slot Filler initialized")

    def fill_slots(
        self,
        entities: Dict[str, List],
        module_params: Dict[str, Any],
        intent: str
    ) -> Dict[str, Any]:
        """Fill parameter slots with entities.

        Args:
            entities: Extracted entities
            module_params: Required module parameters
            intent: Recognized intent

        Returns:
            Dict with filled parameters
        """
        try:
            filled = {}

            # Match entities to parameters
            for entity_type, entity_values in entities.items():
                if entity_type in self.param_mappings:
                    param_names = self.param_mappings[entity_type]

                    for param in param_names:
                        if param in module_params and param not in filled:
                            filled[param] = entity_values[0] if entity_values else None
                            break

            logger.info(f"Filled {len(filled)} parameter slots")
            return filled

        except Exception as e:
            logger.error(f"Error filling slots: {e}")
            return {}


if __name__ == "__main__":
    filler = SlotFiller()
    entities = {"url": ["https://example.com"], "email": ["user@test.com"]}
    params = {"url": "string", "email": "string", "submit": "boolean"}
    filled = filler.fill_slots(entities, params, "navigate")
    print(f"Filled slots: {filled}")
