"""
Conversation Manager

Tracks conversation context across multiple interactions.
Manages conversation history, current state, and context memory.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)


class ConversationManager:
    """Manage conversation state and context."""

    def __init__(self, max_history: int = 10):
        """Initialize conversation manager.

        Args:
            max_history: Maximum conversation turns to keep
        """
        self.conversations = {}
        self.max_history = max_history
        logger.info("Conversation Manager initialized")

    def create_conversation(self, user_id: Optional[str] = None) -> str:
        """Create a new conversation.

        Args:
            user_id: Optional user identifier

        Returns:
            Conversation ID
        """
        conv_id = str(uuid.uuid4())
        self.conversations[conv_id] = {
            "id": conv_id,
            "user_id": user_id,
            "history": [],
            "context": {},
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        logger.info(f"Created conversation: {conv_id}")
        return conv_id

    def add_turn(
        self,
        conv_id: str,
        user_input: str,
        intent: str,
        entities: Dict,
        response: Any
    ):
        """Add a conversation turn.

        Args:
            conv_id: Conversation ID
            user_input: User's input text
            intent: Recognized intent
            entities: Extracted entities
            response: System response
        """
        if conv_id not in self.conversations:
            raise ValueError(f"Conversation not found: {conv_id}")

        conv = self.conversations[conv_id]
        turn = {
            "user_input": user_input,
            "intent": intent,
            "entities": entities,
            "response": response,
            "timestamp": datetime.utcnow().isoformat()
        }

        conv["history"].append(turn)

        # Trim history
        if len(conv["history"]) > self.max_history:
            conv["history"] = conv["history"][-self.max_history:]

        # Update context
        conv["context"]["previous_intent"] = intent
        conv["context"]["previous_entities"] = entities
        conv["updated_at"] = datetime.utcnow().isoformat()

    def get_context(self, conv_id: str) -> Dict[str, Any]:
        """Get conversation context.

        Args:
            conv_id: Conversation ID

        Returns:
            Current context
        """
        if conv_id not in self.conversations:
            return {}

        return self.conversations[conv_id]["context"]

    def get_history(self, conv_id: str, last_n: Optional[int] = None) -> List[Dict]:
        """Get conversation history.

        Args:
            conv_id: Conversation ID
            last_n: Optional number of recent turns

        Returns:
            List of conversation turns
        """
        if conv_id not in self.conversations:
            return []

        history = self.conversations[conv_id]["history"]
        if last_n:
            return history[-last_n:]
        return history


if __name__ == "__main__":
    manager = ConversationManager()
    conv_id = manager.create_conversation("user123")
    manager.add_turn(conv_id, "Create a container", "create", {}, {"success": True})
    print(f"Context: {manager.get_context(conv_id)}")
    print(f"History: {manager.get_history(conv_id)}")
