"""
AI Conversation Executor

Handles AI-powered conversation responses using Claude API.
"""

import os
import json
import logging
from typing import List, Dict, Any
import anthropic

from .models import ConversationContext, AIResponse, Intent, Sentiment

logger = logging.getLogger(__name__)


class AIConversationExecutor:
    """AI-powered conversation handler using Claude"""

    def __init__(self):
        """Initialize Claude API client"""
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            logger.warning("ANTHROPIC_API_KEY not set - AI responses will be disabled")
            self.client = None
        else:
            self.client = anthropic.Anthropic(api_key=api_key)
            logger.info("AI Conversation Executor initialized with Claude 3 Haiku")

        self.model = "claude-3-haiku-20240307"  # Fast and cost-effective for SMS

    async def generate_response(
        self,
        context: ConversationContext,
        inbound_message: str
    ) -> AIResponse:
        """
        Generate AI response based on conversation context and inbound message.

        Args:
            context: Conversation context with contact info and message history
            inbound_message: The incoming message text

        Returns:
            AIResponse with reply text and metadata
        """
        # Check for opt-out keywords first (don't need AI for this)
        if self._is_optout(inbound_message):
            return AIResponse(
                reply_text="You have been unsubscribed. Reply START to resubscribe.",
                intent=Intent.OPTOUT,
                sentiment=Sentiment.NEUTRAL,
                confidence=1.0,
                should_notify_human=False,
                suggested_tags=["opted_out", "dnd"]
            )

        # Check for opt-in keywords
        if self._is_optin(inbound_message):
            return AIResponse(
                reply_text="Welcome back! You have been resubscribed to messages.",
                intent=Intent.OPTIN,
                sentiment=Sentiment.POSITIVE,
                confidence=1.0,
                should_notify_human=False,
                suggested_tags=["opted_in"]
            )

        # If Claude is not available, return fallback
        if not self.client:
            return self._fallback_response(inbound_message)

        try:
            # Build conversation history for context
            messages_context = self._build_message_history(context.recent_messages)

            system_prompt = self._build_system_prompt(context)

            user_message = f"""Previous messages:
{messages_context}

New message from customer: "{inbound_message}"

Generate an appropriate response."""

            # Call Claude API
            response = self.client.messages.create(
                model=self.model,
                max_tokens=500,
                system=system_prompt,
                messages=[{"role": "user", "content": user_message}]
            )

            # Parse AI response
            ai_response = self._parse_ai_response(response.content[0].text)

            logger.info(
                f"AI response generated - Intent: {ai_response.intent}, "
                f"Sentiment: {ai_response.sentiment}, Confidence: {ai_response.confidence}"
            )

            return ai_response

        except Exception as e:
            logger.exception(f"Error generating AI response: {str(e)}")
            return self._fallback_response(inbound_message)

    def _build_system_prompt(self, context: ConversationContext) -> str:
        """Build system prompt with conversation context"""
        return f"""You are a helpful assistant for {context.location_name or 'our business'}.
You're responding to SMS messages from customers.

RULES:
1. Keep responses SHORT (under 160 characters when possible, max 320)
2. Be friendly but professional
3. If customer wants to book/schedule, ask for their preferred date and time
4. If customer has a complaint, acknowledge it and offer to have someone call them
5. Always end with a clear next step or question
6. Never make up information about availability - if unsure, offer to have someone follow up
7. Use simple language and avoid jargon

CUSTOMER INFO:
- Name: {context.contact_name or 'Customer'}
- Has existing appointment: {context.has_appointment}
- Appointment date: {context.appointment_date or 'None'}
- Tags: {', '.join(context.contact_tags) if context.contact_tags else 'None'}

RESPOND WITH JSON:
{{"reply": "your response text", "intent": "booking|question|complaint|confirmation|reschedule|greeting|other", "sentiment": "positive|negative|neutral", "notify_human": true/false, "extracted_data": {{}}}}

Intent options:
- booking: Customer wants to schedule/book something
- question: Customer has a question
- complaint: Customer has a complaint or issue
- confirmation: Customer is confirming something
- reschedule: Customer wants to change appointment
- greeting: Customer is just saying hello
- other: Anything else

Keep your reply concise and friendly!"""

    def _is_optout(self, message: str) -> bool:
        """Check if message is an opt-out request"""
        optout_keywords = ['stop', 'unsubscribe', 'cancel', 'quit', 'end', 'optout', 'opt out']
        message_lower = message.lower().strip()
        return message_lower in optout_keywords

    def _is_optin(self, message: str) -> bool:
        """Check if message is an opt-in request"""
        optin_keywords = ['start', 'subscribe', 'yes', 'optin', 'opt in', 'unstop']
        message_lower = message.lower().strip()
        return message_lower in optin_keywords

    def _build_message_history(self, messages: List[Dict[str, Any]], limit: int = 10) -> str:
        """Build conversation history string from recent messages"""
        if not messages:
            return "(No previous messages)"

        history = []
        for msg in messages[-limit:]:
            direction = "Customer" if msg.get("direction") == "inbound" else "Us"
            body = msg.get("body", "")
            if body:
                history.append(f"{direction}: {body}")

        return "\n".join(history) if history else "(No previous messages)"

    def _parse_ai_response(self, response_text: str) -> AIResponse:
        """Parse AI JSON response into AIResponse model"""
        try:
            # Try to extract JSON from response
            if "{" in response_text and "}" in response_text:
                json_start = response_text.index("{")
                json_end = response_text.rindex("}") + 1
                json_str = response_text[json_start:json_end]
                data = json.loads(json_str)

                return AIResponse(
                    reply_text=data.get("reply", response_text)[:320],  # Truncate to SMS length
                    intent=Intent(data.get("intent", "other")),
                    sentiment=Sentiment(data.get("sentiment", "neutral")),
                    confidence=0.9,
                    should_notify_human=data.get("notify_human", False),
                    extracted_data=data.get("extracted_data", {})
                )
        except Exception as e:
            logger.warning(f"Failed to parse AI JSON response: {e}")

        # Fallback: use raw response
        return AIResponse(
            reply_text=response_text[:320],  # Truncate to SMS length
            intent=Intent.OTHER,
            sentiment=Sentiment.NEUTRAL,
            confidence=0.5,
            should_notify_human=False
        )

    def _fallback_response(self, inbound_message: str) -> AIResponse:
        """Generate fallback response when AI is unavailable"""
        return AIResponse(
            reply_text="Thanks for your message! Someone will get back to you shortly.",
            intent=Intent.OTHER,
            sentiment=Sentiment.NEUTRAL,
            confidence=0.0,
            should_notify_human=True
        )
