from collections import deque
from typing import Deque, Dict, List, Optional


class DialogueManager:
    """
    Sprint 3 v1:
    - son kullanıcı mesajını tutar
    - son bot cevabını tutar
    - son intent'i tutar
    - kısa geçmiş (turn history) saklar
    - basit topic takibi yapar
    - follow-up cümlelerini tespit eder
    """

    def __init__(self, max_turns: int = 4):
        self.max_turns = max_turns

        self.last_user: Optional[str] = None
        self.last_bot: Optional[str] = None
        self.last_intent: Optional[str] = None

        self.history: Deque[Dict[str, str]] = deque(maxlen=max_turns)
        self.current_topic: Optional[str] = None

    # ---------------------------------------------------------
    # PUBLIC API
    # ---------------------------------------------------------
    def update(self, user_text: str, bot_text: str, intent: str) -> None:
        self.last_user = user_text
        self.last_bot = bot_text
        self.last_intent = intent

        self.history.append({
            "user": user_text,
            "bot": bot_text,
            "intent": intent,
        })

        self.current_topic = self._infer_topic(user_text, intent)

    def get_context(self) -> Dict[str, object]:
        return {
            "last_user": self.last_user,
            "last_bot": self.last_bot,
            "last_intent": self.last_intent,
            "current_topic": self.current_topic,
            "history": list(self.history),
        }

    def is_followup(self, text: str) -> bool:
        normalized = self._normalize(text)

        followups = {
            "sonra",
            "e sonra",
            "peki sonra",
            "neden",
            "neden oyle",
            "neden öyle",
            "nasil",
            "nasıl",
            "nasil yani",
            "nasıl yani",
            "emin misin",
            "sonra ne oldu",
            "peki",
            "ee",
            "ee sonra",
        }

        return normalized in followups

    def get_recent_turns_as_text(self, limit: int = 3) -> str:
        if not self.history:
            return ""

        turns = list(self.history)[-limit:]
        lines: List[str] = []
        for item in turns:
            user = item.get("user", "")
            bot = item.get("bot", "")
            if user:
                lines.append(f"Kullanıcı: {user}")
            if bot:
                lines.append(f"Poodle: {bot}")

        return "\n".join(lines).strip()

    # ---------------------------------------------------------
    # INTERNALS
    # ---------------------------------------------------------
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

        if "okul" in normalized or "ders" in normalized or "sinav" in normalized or "sınav" in normalized:
            return "school"

        if "dogum gunu" in normalized or "doğum günü" in user_text.lower():
            return "birthday"

        if "uzgun" in normalized or "üzgün" in user_text.lower() or "moral" in normalized:
            return "emotion"

        if "matematik" in normalized or "fen" in normalized or "ingilizce" in normalized or "lgs" in normalized:
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
        return " ".join(t.split())
