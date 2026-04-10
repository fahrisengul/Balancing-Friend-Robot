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

        # düşük kalite
        if intent in {"low_confidence", "clarification_needed"}:
            return Decision("clarify", "Galiba tam duyamadım. Daha net söyler misin?")

        # deterministic sosyal cevaplar
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

        # deterministic skill
        if intent in {
            "ask_birthdate",
            "ask_age",
            "ask_day_date",
            "ask_time",
            "mute",
            "wake",
        }:
            return Decision("skill")

        # gerçek soru
        if intent in {
            "question",
            "ask_activity",
            "education_help",
            "emotional_support",
            "general",
        }:
            return Decision("llm")

        # statement → kısa ama daha akıllı template
        if intent == "statement":
            return Decision("template")

        return Decision("clarify", "Bunu tam anlayamadım. Biraz daha açık söyler misin?")

    def apply(self, raw: str) -> str:
        if not raw:
            return "Tam anlayamadım. Bir daha söyler misin?"

        text = " ".join(raw.strip().split())

        lowered = text.lower()

        # ❌ persona drift temizliği
        bad_patterns = [
            "ahaha", "hehe", "ooh", "oh dear",
            "hello", "i am",
            "ben poodle", "masaustu robot", "masaüstü robot",
            "kullanici:", "kullanıcı:", "system prompt",
            "robotun adi", "robotun adı",
            "kisa dogal diyalog", "kısa doğal diyalog"
        ]

        if any(p in lowered for p in bad_patterns):
            return "Seni duydum. Biraz daha net anlatır mısın?"

        # ❌ İngilizce kaçakları kes
        if any(word in lowered for word in ["hello", "hi ", "how are you", "i am"]):
            return "Türkçe devam edelim. Ne demek istediğini biraz açar mısın?"

        # ❌ aşırı uzunluk kes
        parts = [p.strip() for p in text.split(".") if p.strip()]
        if len(parts) > 2:
            text = ". ".join(parts[:2]).strip()
            if not text.endswith("."):
                text += "."

        # ❌ anlamsız kısa
        if len(text) < 3:
            return "Biraz daha açık söyler misin?"

        return text
