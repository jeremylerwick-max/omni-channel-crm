"""
Opt-Out Detection Module

Centralized, deterministic opt-out and opt-in detection.
NO AI involved - pure keyword matching for compliance safety.

This module is used by both:
- orchestrator/twilio_webhooks.py (early detection before AI processing)
- modules/ai_conversation/executor.py (fallback, though webhook should catch first)
"""

import re
import logging

logger = logging.getLogger(__name__)

# Comprehensive opt-out patterns
OPT_OUT_KEYWORDS = [
    # Exact matches (case-insensitive)
    "stop", "unsubscribe", "cancel", "quit", "end", "optout", "opt-out",

    # Phrases (must be contained in message)
    "opt out", "remove me", "take me off", "don't text", "dont text",
    "stop texting", "leave me alone", "wrong number", "not interested",
    "do not contact", "never contact", "stop messaging", "stop contacting",
    "unsubscribe me", "remove from list", "take off list", "no more texts",
    "no more messages", "stop sending", "please stop", "pls stop"
]

# Words/phrases that negate opt-out (e.g., "don't stop" or "please don't remove me yet")
OPT_OUT_NEGATIONS = [
    "don't stop", "dont stop", "do not stop",
    "not yet", "keep texting", "keep messaging",
    "don't remove", "dont remove", "do not remove",
    "don't unsubscribe", "dont unsubscribe"
]

# Opt-in keywords
OPT_IN_KEYWORDS = [
    "start", "subscribe", "unstop", "yes", "resume", "optin", "opt-in", "opt in"
]


def is_optout(message: str) -> bool:
    """
    Detect opt-out intent using comprehensive keyword matching.

    This is DETERMINISTIC - no AI involved for compliance safety.

    Args:
        message: The incoming message text

    Returns:
        True if message contains opt-out intent, False otherwise

    Examples:
        >>> is_optout("STOP")
        True
        >>> is_optout("Please stop texting me")
        True
        >>> is_optout("wrong number")
        True
        >>> is_optout("don't stop texting")
        False
        >>> is_optout("Can we stop by your office?")
        False (contextual use)
    """
    if not message or not isinstance(message, str):
        return False

    # Normalize message
    msg_lower = message.lower().strip()

    # Remove punctuation for clean word matching
    msg_clean = ''.join(c for c in msg_lower if c.isalnum() or c.isspace())

    # Check for negations first (these override opt-out detection)
    for negation in OPT_OUT_NEGATIONS:
        if negation in msg_lower:
            logger.debug(f"Opt-out negation detected: '{negation}' in message")
            return False

    # Check exact word matches (message is JUST the keyword)
    words = msg_clean.split()
    exact_keywords = ["stop", "unsubscribe", "cancel", "quit", "end", "optout"]

    # Single word message that is an exact match
    if len(words) == 1 and words[0] in exact_keywords:
        logger.info(f"Exact opt-out keyword detected: '{words[0]}'")
        return True

    # Check phrase containment (keyword appears in message)
    for phrase in OPT_OUT_KEYWORDS:
        if phrase in msg_lower:
            # Additional validation for common words like "stop" to avoid false positives
            if phrase == "stop":
                # "stop" is only opt-out if:
                # - It's the only word, OR
                # - It's followed by "texting", "messaging", "contacting", "sending", etc., OR
                # - The message is very short (< 20 chars), OR
                # - It appears at the start: "stop please", "stop this"
                if (len(msg_clean) < 20 or
                    msg_lower.startswith("stop") or
                    any(w in msg_lower for w in ["stop text", "stop messag", "stop contact", "stop send", "pls stop", "please stop"])):
                    logger.info(f"Opt-out phrase detected: '{phrase}' in message")
                    return True
            else:
                # All other phrases are definitive opt-outs
                logger.info(f"Opt-out phrase detected: '{phrase}' in message")
                return True

    return False


def is_optin(message: str) -> bool:
    """
    Detect opt-in/resubscribe intent.

    Args:
        message: The incoming message text

    Returns:
        True if message contains opt-in intent, False otherwise

    Examples:
        >>> is_optin("START")
        True
        >>> is_optin("yes subscribe")
        True
        >>> is_optin("unstop")
        True
    """
    if not message or not isinstance(message, str):
        return False

    msg_lower = message.lower().strip()
    msg_clean = ''.join(c for c in msg_lower if c.isalnum() or c.isspace())
    words = msg_clean.split()

    # Check exact word matches
    for keyword in OPT_IN_KEYWORDS:
        keyword_clean = ''.join(c for c in keyword if c.isalnum() or c.isspace())
        if keyword_clean in words:
            logger.info(f"Opt-in keyword detected: '{keyword}'")
            return True

    # Check phrase containment
    for keyword in OPT_IN_KEYWORDS:
        if keyword in msg_lower:
            logger.info(f"Opt-in phrase detected: '{keyword}'")
            return True

    return False
