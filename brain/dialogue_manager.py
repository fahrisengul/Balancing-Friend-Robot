import time
from collections import deque


class DialogueManager:
    def __init__(self):
        self.history = deque(maxlen=10)
        self.current_topic = None
        self.last_intent = None
        self.last_user = None
        self.last_bot = None
        self.last_time = time.time()

    def update(self, user_text: str, bot_text: str, intent: str):
        now = time.time()

        self.history.append({
            "user": user_text,
            "bot": bot_text,
            "intent": intent,
            "time": now
        })

        self.last_user = user_text
        self.last_bot = bot_text
        self.last_intent = intent
        self.last_time = now

        # -------------------------------------------------
        # TOPIC DETECTION (basit ama etkili)
        # -------------------------------------------------
        if intent in {"education_help"}:
            self.current_topic = "education"

        elif intent in {"emotional_support"}:
            self.current_topic = "emotion"

        elif intent in {"ask_activity", "question"}:
            self.current_topic = "general"

        elif intent == "followup":
            # topic korunur
            pass

        elif intent == "farewell":
            self.current_topic = None

    # -------------------------------------------------
    # CONTEXT
    # -------------------------------------------------
    def get_context(self):
        return {
            "last_user": self.last_user,
            "last_bot": self.last_bot,
            "last_intent": self.last_intent,
            "current_topic": self.current_topic
        }

    def get_recent_turns_as_text(self, limit=3):
        turns = list(self.history)[-limit:]
        lines = []
        for t in turns:
            lines.append(f"Kullanıcı: {t['user']}")
            lines.append(f"Poodle: {t['bot']}")
        return "\n".join(lines)

    def get_current_topic(self):
        return self.current_topic
