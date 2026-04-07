from collections import deque
from typing import Dict, Optional


class DialogueManager:

    def __init__(self, max_turns: int = 6):
        self.history = deque(maxlen=max_turns)
        self.current_topic: Optional[str] = None
        self.last_intent: Optional[str] = None

    def update(self, user_text: str, bot_reply: str, intent: str):
        self.history.append({
            "user": user_text,
            "bot": bot_reply,
            "intent": intent
        })

        self.last_intent = intent

        inferred_topic = self._infer_topic(user_text, intent)
        if inferred_topic:
            self.current_topic = inferred_topic

    def get_context(self) -> Dict:
        last_turn = self.history[-1] if self.history else {}

        return {
            "last_user": last_turn.get("user"),
            "last_bot": last_turn.get("bot"),
            "last_intent": last_turn.get("intent"),
            "current_topic": self.current_topic,
        }

    def _infer_topic(self, user_text: str, intent: str) -> Optional[str]:
        normalized = self._normalize(user_text)

        if intent in {"ask_birthdate", "ask_age"}:
            return "birthday"

        if intent in {"ask_name", "ask_identity"}:
            return "identity"

        if intent in {"ask_status", "emotional_support"}:
            return "emotion"

        if intent in {"education_help"}:
            return "education"

        if intent == "ask_activity":
            return "daily_life"

        if intent == "followup":
            return self.current_topic

        if "okul" in normalized or "ders" in normalized or "sinav" in normalized:
            return "school"

        if "dogum gunu" in normalized:
            return "birthday"

        if "uzgun" in normalized or "moral" in normalized:
            return "emotion"

        if "matematik" in normalized or "fen" in normalized:
            return "education"

        return self.current_topic

    def _normalize(self, text: str) -> str:
        t = (text or "").lower().strip()
        t = (
            t.replace("ı", "i")
             .replace("ğ", "g")
             .replace("ş", "s")
             .replace("ç", "c")
             .replace("ö", "o")
             .replace("ü", "u")
        )
        return t
