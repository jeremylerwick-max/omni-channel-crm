"""
AI Conversation Module

Handles AI-powered conversation responses using Claude API.
"""

from .models import (
    Intent,
    Sentiment,
    ConversationContext,
    AIResponse,
    OptOutRequest
)
from .executor import AIConversationExecutor

__all__ = [
    'Intent',
    'Sentiment',
    'ConversationContext',
    'AIResponse',
    'OptOutRequest',
    'AIConversationExecutor'
]
