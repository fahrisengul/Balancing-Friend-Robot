from dataclasses import dataclass
from typing import Optional


@dataclass
class PolicyDecision:
    source: str
    clarify_text: Optional[str] = None


class ResponsePolicy:
    """
    source değerleri:
    - clarify
    - skill
    - template
    - llm
    """

    def choose_source(self, text: str, intent: str) -> PolicyDecision:
        normalized = (text or "").strip().lower()

        if not normalized:
            return PolicyDecision(
                source="clarify",
                clarify_text="Seni tam anlayamadım. Bir kez daha söyler misin?"
            )

        if intent in {"low_confidence", "clarification_needed"}:
            return PolicyDecision(
                source="clarify",
                clarify_text="Son söylediğini tam çıkaramadım. Bir kez daha söyler misin?"
            )

        # Sosyal kısa cevaplar template'ten gelsin
        template_intents = {
            "greeting",
            "ask_name",
            "ask_identity",
            "ask_status",
            "thanks",
            "acknowledge",
            "followup",
            "smalltalk_short",
        }
        if intent in template_intents:
            return PolicyDecision(source="template")

        # Kesin bilgi / hesap / cihaz davranışı skill
        deterministic_skill_intents = {
            "ask_birthdate",
            "ask_age",
            "ask_day_date",
            "ask_time",
            "mute",
            "wake",
        }
        if intent in deterministic_skill_intents:
            return PolicyDecision(source="skill")

        llm_intents = {
            "general",
            "ask_activity",
            "free_talk",
            "education_help",
            "emotional_support",
        }
        if intent in llm_intents:
            return PolicyDecision(source="llm")

        return PolicyDecision(
            source="clarify",
            clarify_text="Bunu tam anlayamadım. Biraz daha açık söyler misin?"
        )

    def apply(self, text: str) -> str:
        cleaned = (text or "").strip()
        if not cleaned:
            return "Bunu tam anlayamadım. Bir kez daha söyler misin?"

        cleaned = " ".join(cleaned.split())

        parts = cleaned.split(".")
        if len(parts) > 2:
            cleaned = ".".join(parts[:2]).strip()
            if cleaned and not cleaned.endswith("."):
                cleaned += "."

        robotic_markers = [
            "ben sen poodle",
            "görevim",
            "robot arkadaşındır",
            "kullanıcı:",
            "görev:",
            "system prompt",
        ]
        lower = cleaned.lower()
        if any(marker in lower for marker in robotic_markers):
            return "Bunu daha sade söyleyeyim: seni anladım. Biraz daha anlatmak ister misin?"

        if lower in {"52", "iyi şey", "tamam işte"}:
            return "Bundan tam emin değilim. Biraz daha açık sorar mısın?"

        return cleaned
