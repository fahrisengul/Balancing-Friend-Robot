from collections import deque
from typing import Deque, Dict, List, Optional


class DialogueManager:
    def __init__(self, max_turns: int = 6):
        self.max_turns = max_turns
        self.last_user: Optional[str] = None
        self.last_bot: Optional[str] = None
        self.last_intent: Optional[str] = None
        self.current_topic: Optional[str] = None
        self.history: Deque[Dict[str, str]] = deque(maxlen=max_turns)

    def update(self, user_text: str, bot_text: str, intent: str) -> None:
        self.last_user = user_text
        self.last_bot = bot_text
        self.last_intent = intent

        self.history.append({
            "user": user_text,
            "bot": bot_text,
            "intent": intent,
        })

        inferred = self._infer_topic(user_text, intent)
        if inferred:
            self.current_topic = inferred

    def get_context(self) -> Dict[str, object]:
        return {
            "last_user": self.last_user,
            "last_bot": self.last_bot,
            "last_intent": self.last_intent,
            "current_topic": self.current_topic,
            "history": list(self.history),
        }

    def get_recent_turns_as_text(self, limit: int = 3) -> str:
        if not self.history:
            return ""

        turns = list(self.history)[-limit:]
        lines: List[str] = []

        for turn in turns:
            user = turn.get("user", "").strip()
            bot = turn.get("bot", "").strip()
            if user:
                lines.append(f"Kullanıcı: {user}")
            if bot:
                lines.append(f"Poodle: {bot}")

        return "\n".join(lines).strip()

    def _infer_topic(self, user_text: str, intent: str) -> Optional[str]:
        n = self._normalize(user_text)

        if intent in {"ask_name", "ask_identity"}:
            return "identity"

        if intent in {"ask_status", "emotional_support"}:
            return "emotion"

        if intent in {"ask_birthdate", "ask_age"}:
            return "birthday"

        if intent in {"ask_activity"}:
            return "daily_life"

        if intent in {"education_help"}:
            return "education"

        if intent in {"followup_repair"}:
            return self.current_topic

        if any(x in n for x in ["ders", "sinav", "motivasyon", "matematik", "lgs"]):
            return "education"

        if any(x in n for x in ["bugun", "gun", "dolastin", "dolaştın", "neler yaptin", "ne yaptin"]):
            return "daily_life"

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
        return " ".join(t.split())
