from dataclasses import dataclass
from typing import Optional


@dataclass
class Decision:
    source: str
    clarify_text: Optional[str] = None


class ResponsePolicy:
    """
    source:
    - clarify
    - template
    - skill
    - llm
    """

    def choose_source(self, text: str, intent: str) -> Decision:
        t = (text or "").strip().lower()

        if not t:
            return Decision("clarify", "Seni tam anlayamadım. Tekrar söyler misin?")

        # 🚨 CRITICAL FIX: conversational intents
        conversational_intents = {
            "conversation_start",
            "ask_question_back",
            "ask_topic",
            "open_topic",
        }

        if intent in conversational_intents:
            return Decision("template")

        if intent in {"low_confidence", "clarification_needed"}:
            return Decision("clarify", "Galiba tam duyamadım. Daha net söyler misin?")

        if intent in {
            "greeting",
            "farewell",
            "ask_name",
            "ask_identity",
            "ask_status",
            "thanks",
            "acknowledge",
            "followup",
            "followup_repair",
        }:
            return Decision("template")

        if intent in {
            "ask_birthdate",
            "ask_age",
            "ask_day_date",
            "ask_time",
            "mute",
            "wake",
        }:
            return Decision("skill")

        # 🎯 geri kalan → LLM
        return Decision("llm")

    def apply(self, raw: str) -> str:
        if not raw:
            return "Biraz daha açık söyler misin?"

        text = " ".join(raw.strip().split())
        lowered = text.lower()

        # ❌ prompt leak filtre
        bad_patterns = [
            "kisa dogal diyalog",
            "robotun adı poodle",
            "system prompt",
        ]

        if any(p in lowered for p in bad_patterns):
            return "Seni duydum. Biraz daha net anlatır mısın?"

        # ❌ İngilizce kaçak
        if any(word in lowered for word in ["hello", "hi ", "how are you", "i am"]):
            return "Türkçe devam edelim. Ne demek istediğini biraz açar mısın?"

        # ❌ çok uzun kes
        parts = [p.strip() for p in text.split(".") if p.strip()]
        if len(parts) > 2:
            text = ". ".join(parts[:2]).strip()
            if not text.endswith("."):
                text += "."

        # ❌ çok kısa
        if len(text) < 3:
            return "Biraz daha açık söyler misin?"

        return text
