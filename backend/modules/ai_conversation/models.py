"""
AI Conversation Models

Pydantic models for AI-powered conversation handling.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum


class Intent(str, Enum):
    """Message intent classification"""
    BOOKING = "booking"
    QUESTION = "question"
    COMPLAINT = "complaint"
    OPTOUT = "optout"
    OPTIN = "optin"
    CONFIRMATION = "confirmation"
    RESCHEDULE = "reschedule"
    GREETING = "greeting"
    OTHER = "other"


class Sentiment(str, Enum):
    """Message sentiment classification"""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


class ConversationContext(BaseModel):
    """Context for generating AI responses"""
    contact_id: str
    contact_name: Optional[str] = None
    conversation_id: str
    recent_messages: List[Dict[str, Any]] = Field(default_factory=list)
    contact_tags: List[str] = Field(default_factory=list)
    has_appointment: bool = False
    appointment_date: Optional[str] = None
    location_name: Optional[str] = None
    location_timezone: str = "America/Chicago"


class AIResponse(BaseModel):
    """AI-generated response with metadata"""
    reply_text: str
    intent: Intent
    sentiment: Sentiment
    confidence: float = Field(ge=0.0, le=1.0)
    should_notify_human: bool = False
    suggested_tags: List[str] = Field(default_factory=list)
    extracted_data: Dict[str, Any] = Field(default_factory=dict)


class OptOutRequest(BaseModel):
    """Request to opt-out a contact"""
    contact_id: str
    reason: str = "Customer requested STOP"
