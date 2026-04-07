from collections import deque
from typing import Deque, Dict, List, Optional


class DialogueManager:
    """
    Sprint 3/4 final:
    - son kullanıcı mesajı
    - son bot cevabı
    - son intent
    - kısa konuşma geçmişi
    - topic continuity
    - follow-up destekli bağlam
    """

    def __init__(self, max_turns: int = 6):
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

        inferred_topic = self._infer_topic(user_text, intent)
        if inferred_topic:
            self.current_topic = inferred_topic

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

        for item in turns:
            user = item.get("user", "").strip()
            bot = item.get("bot", "").strip()

            if user:
                lines.append(f"Kullanıcı: {user}")
            if bot:
                lines.append(f"Poodle: {bot}")

        return "\n".join(lines).strip()

    def is_followup(self, text: str) -> bool:
        normalized = self._normalize(text)

        followup_phrases = {
            "sonra",
            "e sonra",
            "ee sonra",
            "peki sonra",
            "neden",
            "neden oyle",
            "nasil",
            "nasil yani",
            "emin misin",
            "sonra ne oldu",
            "ne anladin",
            "ne dedin",
            "ne demek istedin",
            "yani",
            "peki",
            "ee",
        }

        return normalized in followup_phrases

    # ---------------------------------------------------------
    # INTERNALS
    # ---------------------------------------------------------
    def _infer_topic(self, user_text: str, intent: str) -> Optional[str]:
        normalized = self._normalize(user_text)

        # Intent bazlı güçlü eşleşme
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

        # Keyword bazlı eşleşme
        if any(k in normalized for k in {"okul", "ders", "sinav"}):
            return "school"

        if "dogum gunu" in normalized:
            return "birthday"

        if any(k in normalized for k in {"uzgun", "moral", "kotu hissediyorum"}):
            return "emotion"

        if any(k in normalized for k in {"matematik", "fen", "ingilizce", "lgs"}):
            return "education"

        if any(k in normalized for k in {"bugun", "yaptim", "yapiyorum", "gunum"}):
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
