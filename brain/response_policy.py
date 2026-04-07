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

        # düşük güvenli / bozuk / anlamsız giriş
        if intent in {"low_confidence", "clarification_needed"}:
            return Decision("clarify", "Galiba tam duyamadım. Daha net söyler misin?")

        # kısa deterministic sosyal cevaplar
        if intent in {
            "greeting",
            "farewell",
            "ask_name",
            "ask_identity",
            "ask_status",
            "thanks",
            "acknowledge",
            "followup_repair",
        }:
            return Decision("template")

        # saat / tarih / yaş / doğum günü gibi deterministic skill'ler
        if intent in {
            "ask_birthdate",
            "ask_age",
            "ask_day_date",
            "ask_time",
            "mute",
            "wake",
        }:
            return Decision("skill")

        # gerçek soru → LLM
        if intent in {"question", "ask_activity", "education_help", "emotional_support", "general"}:
            return Decision("llm")

        # statement'lar için kısa template
        if intent == "statement":
            return Decision("template")

        return Decision("clarify", "Bunu tam çıkaramadım. Biraz daha açık söyler misin?")

    def apply(self, raw: str) -> str:
        if not raw:
            return "Tam anlayamadım. Bir daha söyler misin?"

        text = " ".join(raw.strip().split())

        # prompt leakage / persona drift temizliği
        bad_markers = [
            "ahaha", "hehe", "ooh", "oh dear", "hello",
            "ben poodle", "masaustu robot", "masaüstü robot",
            "kullanici:", "kullanıcı:", "system prompt",
            "robotun adi poodle", "robotun adı poodle",
            "kisa dogal diyalog", "kısa doğal diyalog"
        ]
        lowered = text.lower()
        if any(m in lowered for m in bad_markers):
            return "Bunu daha sade söyleyeyim: seni duydum. Biraz daha açık anlatır mısın?"

        # çok uzun cevapları kısalt
        parts = [p.strip() for p in text.split(".") if p.strip()]
        if len(parts) > 2:
            text = ". ".join(parts[:2]).strip()
            if not text.endswith("."):
                text += "."

        # son güvenlik
        if len(text) < 2:
            return "Biraz daha açık söyler misin?"

        return text
