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

        # 2) Düşük güvenli input
        if intent in {"low_confidence", "clarification_needed"}:
            return PolicyDecision(
                source="clarify",
                clarify_text="Son söylediğini tam çıkaramadım. Bir kez daha söyler misin?"
            )

        # 3) Template ile cevaplanacak sosyal / kısa intent'ler
        template_intents = {
            "greeting",
            "ask_name",
            "ask_identity",
            "ask_status",
            "thanks",
            "acknowledge",
            "smalltalk_short",
        }
        if intent in template_intents:
            return PolicyDecision(source="template")

        # 4) Follow-up intent’leri
        # Follow-up için tek başına "Anladım." dönmek yerine template fallback kullanılsın.
        if intent == "followup":
            return PolicyDecision(source="template")

        # 5) Deterministic skill intent'leri
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

        # 6) Açık uçlu konuşmalar
        llm_intents = {
            "general",
            "ask_activity",
            "free_talk",
            "education_help",
            "emotional_support",
        }
        if intent in llm_intents:
            return PolicyDecision(source="llm")

        # 7) Güvenli fallback
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

        cleaned = " ".join(cleaned.split())

        # Çok uzunsa kısalt
        parts = cleaned.split(".")
        if len(parts) > 2:
            cleaned = ".".join(parts[:2]).strip()
            if cleaned and not cleaned.endswith("."):
                cleaned += "."

        # Prompt leakage / robotik ifade temizliği
        robotic_markers = [
            "ben sen poodle",
            "gorevim",
            "robot arkadasinim",
            "robot arkadasindirim",
            "kullanici:",
            "gorev:",
            "system prompt",
            "onceki kisa konusma:",
            "ilgili hafiza:",
            "mevcut konu:",
        ]
        lower = self._normalize(cleaned)
        if any(marker in lower for marker in robotic_markers):
            return "Seni anladım. Bunu biraz daha doğal konuşalım istersen."

        # Çok kısa ama anlamsız saçmalamalar
        if lower in {"52", "iyi sey", "tamam iste"}:
            return "Bundan tam emin değilim. Biraz daha açık sorar mısın?"

        # Fazla genel fallback’leri temizle
        if lower == "anladim":
            return "Seni duydum. Biraz daha açık anlatır mısın?"

        return cleaned

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
