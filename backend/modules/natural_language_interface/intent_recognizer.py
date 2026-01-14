"""
Intent Recognizer

Analyzes user input to determine their intent and map it to module actions.
Supports:
- Intent classification
- Module mapping
- Confidence scoring
- Ambiguity resolution
"""

import re
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class Intent(Enum):
    """Common user intents."""
    # CRUD operations
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    LIST = "list"

    # Actions
    EXECUTE = "execute"
    RUN = "run"
    START = "start"
    STOP = "stop"
    PAUSE = "pause"
    RESUME = "resume"

    # Query operations
    SEARCH = "search"
    FIND = "find"
    GET = "get"
    SHOW = "show"

    # Browser operations
    NAVIGATE = "navigate"
    CLICK = "click"
    FILL = "fill"
    SCRAPE = "scrape"
    SCREENSHOT = "screenshot"

    # File operations
    UPLOAD = "upload"
    DOWNLOAD = "download"
    SAVE = "save"
    LOAD = "load"

    # Communication
    SEND = "send"
    POST = "post"
    MESSAGE = "message"
    EMAIL = "email"

    # Scheduling
    SCHEDULE = "schedule"
    REMIND = "remind"
    REPEAT = "repeat"

    # Analysis
    ANALYZE = "analyze"
    SUMMARIZE = "summarize"
    EXTRACT = "extract"
    TRANSLATE = "translate"

    # System
    HELP = "help"
    STATUS = "status"
    CANCEL = "cancel"
    UNKNOWN = "unknown"


class IntentRecognizer:
    """Recognizes user intent from natural language input."""

    def __init__(self):
        """Initialize intent recognizer."""
        # Intent patterns (keywords that indicate specific intents)
        self.intent_patterns = {
            Intent.CREATE: [
                r'\b(create|make|build|generate|new|add)\b',
                r'\b(set up|setup)\b'
            ],
            Intent.READ: [
                r'\b(read|view|check|see|look at)\b',
                r'\b(what is|what\'s|show me)\b'
            ],
            Intent.UPDATE: [
                r'\b(update|change|modify|edit|alter)\b',
                r'\b(set|configure)\b'
            ],
            Intent.DELETE: [
                r'\b(delete|remove|destroy|erase|clear)\b'
            ],
            Intent.LIST: [
                r'\b(list|show all|get all|enumerate)\b',
                r'\b(what are|tell me all)\b'
            ],
            Intent.EXECUTE: [
                r'\b(execute|run|perform|do|carry out)\b',
                r'\b(trigger|invoke|call)\b'
            ],
            Intent.START: [
                r'\b(start|begin|launch|initiate|boot)\b'
            ],
            Intent.STOP: [
                r'\b(stop|end|terminate|kill|shut down)\b'
            ],
            Intent.PAUSE: [
                r'\b(pause|suspend|hibernate|freeze)\b'
            ],
            Intent.RESUME: [
                r'\b(resume|continue|unpause|wake)\b'
            ],
            Intent.SEARCH: [
                r'\b(search|query|lookup|look up)\b',
                r'\b(find|locate)\b'
            ],
            Intent.FIND: [
                r'\b(find|locate|discover)\b',
                r'\b(where is|where\'s)\b'
            ],
            Intent.GET: [
                r'\b(get|fetch|retrieve|obtain)\b'
            ],
            Intent.SHOW: [
                r'\b(show|display|present)\b'
            ],
            Intent.NAVIGATE: [
                r'\b(navigate to|go to|open|visit)\b',
                r'\b(browse to)\b'
            ],
            Intent.CLICK: [
                r'\b(click|press|tap|select)\b'
            ],
            Intent.FILL: [
                r'\b(fill|fill out|complete|enter|type)\b'
            ],
            Intent.SCRAPE: [
                r'\b(scrape|extract data|harvest|collect data)\b'
            ],
            Intent.SCREENSHOT: [
                r'\b(screenshot|capture|snap|take picture)\b'
            ],
            Intent.UPLOAD: [
                r'\b(upload|send file|attach)\b'
            ],
            Intent.DOWNLOAD: [
                r'\b(download|save|grab|pull)\b'
            ],
            Intent.SAVE: [
                r'\b(save|store|persist|write)\b'
            ],
            Intent.LOAD: [
                r'\b(load|restore|import)\b'
            ],
            Intent.SEND: [
                r'\b(send|transmit|deliver)\b'
            ],
            Intent.POST: [
                r'\b(post|publish|share)\b'
            ],
            Intent.MESSAGE: [
                r'\b(message|text|dm|direct message)\b'
            ],
            Intent.EMAIL: [
                r'\b(email|mail|send email)\b'
            ],
            Intent.SCHEDULE: [
                r'\b(schedule|plan|arrange|book)\b',
                r'\b(set up for|setup for)\b'
            ],
            Intent.REMIND: [
                r'\b(remind|notify|alert)\b'
            ],
            Intent.REPEAT: [
                r'\b(repeat|loop|recur|every)\b'
            ],
            Intent.ANALYZE: [
                r'\b(analyze|examine|inspect|study)\b'
            ],
            Intent.SUMMARIZE: [
                r'\b(summarize|sum up|brief|overview)\b'
            ],
            Intent.EXTRACT: [
                r'\b(extract|pull out|get|parse)\b'
            ],
            Intent.TRANSLATE: [
                r'\b(translate|convert|transform)\b'
            ],
            Intent.HELP: [
                r'\b(help|assist|support)\b',
                r'\b(how do i|how to|can you help)\b'
            ],
            Intent.STATUS: [
                r'\b(status|state|condition|health)\b',
                r'\b(how is|what\'s the state)\b'
            ],
            Intent.CANCEL: [
                r'\b(cancel|abort|undo)\b'
            ]
        }

        # Module intent mapping (which modules handle which intents)
        self.module_intent_map = {
            "docker_sandbox": [Intent.CREATE, Intent.START, Intent.STOP, Intent.EXECUTE, Intent.PAUSE, Intent.RESUME],
            "file_operations": [Intent.CREATE, Intent.READ, Intent.UPDATE, Intent.DELETE, Intent.SAVE, Intent.LOAD, Intent.SEARCH],
            "secret_management": [Intent.CREATE, Intent.READ, Intent.UPDATE, Intent.DELETE, Intent.GET],
            "task_scheduler": [Intent.SCHEDULE, Intent.CREATE, Intent.DELETE, Intent.REPEAT, Intent.REMIND],
            "browser_automation": [Intent.NAVIGATE, Intent.CLICK, Intent.FILL, Intent.SCRAPE, Intent.SCREENSHOT],
            "llm_router": [Intent.ANALYZE, Intent.SUMMARIZE, Intent.TRANSLATE, Intent.EXTRACT, Intent.EXECUTE]
        }

        logger.info("Intent Recognizer initialized")

    def recognize(self, text: str) -> Dict[str, Any]:
        """Recognize intent from text.

        Args:
            text: User input text

        Returns:
            Dict with intent, confidence, and potential modules
        """
        try:
            text_lower = text.lower().strip()

            # Match intents
            intent_scores = {}
            for intent, patterns in self.intent_patterns.items():
                score = 0
                for pattern in patterns:
                    if re.search(pattern, text_lower):
                        score += 1

                if score > 0:
                    intent_scores[intent] = score

            # No matches
            if not intent_scores:
                return {
                    "intent": Intent.UNKNOWN.value,
                    "confidence": 0.0,
                    "modules": [],
                    "alternatives": [],
                    "recognized_at": datetime.utcnow().isoformat()
                }

            # Sort by score
            sorted_intents = sorted(intent_scores.items(), key=lambda x: x[1], reverse=True)
            primary_intent, primary_score = sorted_intents[0]

            # Calculate confidence (normalize by max possible matches)
            max_patterns = len(self.intent_patterns[primary_intent])
            confidence = min(primary_score / max_patterns, 1.0)

            # Get potential modules
            modules = self._get_modules_for_intent(primary_intent)

            # Get alternatives
            alternatives = [
                {
                    "intent": intent.value,
                    "confidence": min(score / len(self.intent_patterns[intent]), 1.0),
                    "modules": self._get_modules_for_intent(intent)
                }
                for intent, score in sorted_intents[1:3]  # Top 2 alternatives
            ]

            result = {
                "intent": primary_intent.value,
                "confidence": round(confidence, 2),
                "modules": modules,
                "alternatives": alternatives,
                "recognized_at": datetime.utcnow().isoformat()
            }

            logger.info(f"Recognized intent: {primary_intent.value} (confidence: {confidence:.2f})")
            return result

        except Exception as e:
            logger.error(f"Error recognizing intent: {e}")
            raise

    def recognize_with_context(
        self,
        text: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Recognize intent with conversation context.

        Args:
            text: User input text
            context: Previous conversation context

        Returns:
            Dict with intent and context-aware information
        """
        try:
            # Basic recognition
            result = self.recognize(text)

            # Apply context if available
            if context:
                # If previous module was specified, prioritize it
                if "previous_module" in context:
                    prev_module = context["previous_module"]
                    if prev_module in result["modules"]:
                        # Move to first position
                        result["modules"].remove(prev_module)
                        result["modules"].insert(0, prev_module)

                # Boost confidence if intent matches previous intent
                if "previous_intent" in context:
                    if result["intent"] == context["previous_intent"]:
                        result["confidence"] = min(result["confidence"] + 0.1, 1.0)
                        result["context_boost"] = True

            return result

        except Exception as e:
            logger.error(f"Error recognizing intent with context: {e}")
            raise

    def _get_modules_for_intent(self, intent: Intent) -> List[str]:
        """Get modules that can handle an intent.

        Args:
            intent: The intent

        Returns:
            List of module names
        """
        modules = []
        for module, intents in self.module_intent_map.items():
            if intent in intents:
                modules.append(module)

        return modules

    def suggest_modules(self, text: str) -> List[Dict[str, Any]]:
        """Suggest modules based on keywords in text.

        Args:
            text: User input text

        Returns:
            List of module suggestions with reasons
        """
        try:
            suggestions = []
            text_lower = text.lower()

            # Keyword-based module detection
            module_keywords = {
                "docker_sandbox": ["container", "docker", "sandbox", "isolate"],
                "file_operations": ["file", "directory", "folder", "document", "compress", "encrypt"],
                "secret_management": ["secret", "password", "api key", "credential", "token"],
                "task_scheduler": ["schedule", "cron", "timer", "recurring", "every day"],
                "browser_automation": ["browser", "webpage", "website", "form", "scrape", "url"],
                "llm_router": ["llm", "gpt", "claude", "ai", "summarize", "translate"]
            }

            for module, keywords in module_keywords.items():
                matches = [kw for kw in keywords if kw in text_lower]
                if matches:
                    suggestions.append({
                        "module": module,
                        "confidence": len(matches) / len(keywords),
                        "matched_keywords": matches
                    })

            # Sort by confidence
            suggestions.sort(key=lambda x: x["confidence"], reverse=True)

            return suggestions

        except Exception as e:
            logger.error(f"Error suggesting modules: {e}")
            raise


if __name__ == "__main__":
    # Test intent recognizer
    recognizer = IntentRecognizer()

    # Test 1: Create intent
    print("Test 1: Create intent")
    result = recognizer.recognize("Create a new container with Python 3.9")
    print(f"Intent: {result['intent']}")
    print(f"Confidence: {result['confidence']}")
    print(f"Modules: {result['modules']}")
    print()

    # Test 2: Navigate intent
    print("Test 2: Navigate intent")
    result = recognizer.recognize("Navigate to google.com and fill out the search form")
    print(f"Intent: {result['intent']}")
    print(f"Confidence: {result['confidence']}")
    print(f"Modules: {result['modules']}")
    print()

    # Test 3: Schedule intent
    print("Test 3: Schedule intent")
    result = recognizer.recognize("Schedule a daily backup at 2am")
    print(f"Intent: {result['intent']}")
    print(f"Confidence: {result['confidence']}")
    print(f"Modules: {result['modules']}")
    print()

    # Test 4: Module suggestions
    print("Test 4: Module suggestions")
    suggestions = recognizer.suggest_modules("I need to encrypt a file and store the password securely")
    for suggestion in suggestions:
        print(f"Module: {suggestion['module']} (confidence: {suggestion['confidence']:.2f})")
        print(f"  Matched keywords: {suggestion['matched_keywords']}")
