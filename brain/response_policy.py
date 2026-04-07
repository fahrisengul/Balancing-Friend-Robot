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

        # 1) Boş / anlamsız
        if not normalized:
            return PolicyDecision(
                source="clarify",
                clarify_text="Seni tam anlayamadım. Bir kez daha söyler misin?"
            )

        # 2) Düşük güvenli / belirsiz input intent'i
        if intent in {"low_confidence", "clarification_needed"}:
            return PolicyDecision(
                source="clarify",
                clarify_text="Son söylediğini tam çıkaramadım. Bir kez daha söyler misin?"
            )

        # 3) Asla deterministic skill / template dışına çıkmaması gerekenler
        deterministic_intents = {
            "greeting",
            "ask_name",
            "ask_identity",
            "ask_status",
            "thanks",
            "acknowledge",
            "ask_birthdate",
            "ask_age",
            "ask_day_date",
            "ask_time",
            "mute",
            "wake",
        }
        if intent in deterministic_intents:
            return PolicyDecision(source="skill")

        # 4) Basit kısa sosyal cevaplar template olabilir
        template_intents = {
            "smalltalk_short",
        }
        if intent in template_intents:
            return PolicyDecision(source="template")

        # 5) Açık uçlu konuşmalar LLM
        llm_intents = {
            "general",
            "ask_activity",
            "free_talk",
            "education_help",
            "emotional_support",
            "followup",
        }
        if intent in llm_intents:
            return PolicyDecision(source="llm")

        # 6) Güvenli fallback
        return PolicyDecision(
            source="clarify",
            clarify_text="Bunu tam anlayamadım. Biraz daha açık söyler misin?"
        )

    def apply(self, text: str) -> str:
        """
        LLM çıktısı için son katman sadeleştirme.
        """
        cleaned = (text or "").strip()
        if not cleaned:
            return "Bunu tam anlayamadım. Bir kez daha söyler misin?"

        # gereksiz satır sonları / boşluklar
        cleaned = " ".join(cleaned.split())

        # çok uzunsa kısalt
        parts = cleaned.split(".")
        if len(parts) > 2:
            cleaned = ".".join(parts[:2]).strip()
            if cleaned and not cleaned.endswith("."):
                cleaned += "."

        # belirgin prompt leakage / robotik ifade
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

        # çok kısa ama saçma fallback
        if lower in {"52", "iyi şey", "tamam işte"}:
            return "Bundan tam emin değilim. Biraz daha açık sorar mısın?"

        return cleaned
