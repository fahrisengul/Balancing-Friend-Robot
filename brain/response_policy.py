from dataclasses import dataclass
from typing import Optional


@dataclass
class Decision:
    source: str
    clarify_text: Optional[str] = None


class ResponsePolicy:

    def choose_source(self, text: str, intent: str) -> Decision:
        t = (text or "").strip().lower()

        if not t:
            return Decision("clarify", "Seni tam anlayamadım. Tekrar söyler misin?")

        conversational_intents = {
            "conversation_start",
            "ask_question_back",
            "ask_topic",
            "open_topic",
        }

        if intent in conversational_intents:
            return Decision("template")

        if intent in {"low_confidence", "clarification_needed"}:
            return Decision("clarify", "Tam duyamadım. Bir daha söyler misin?")

        if intent in {
            "greeting",
            "farewell",
            "ask_name",
            "ask_identity",
            "ask_status",
            "thanks",
            "acknowledge",
            "followup",
        }:
            return Decision("template")

        if intent in {
            "ask_birthdate",
            "ask_age",
            "ask_day_date",
            "ask_time",
        }:
            return Decision("skill")

        return Decision("llm")

    # -------------------------------------------------
    # 🔥 DOĞALLIK MOTORU
    # -------------------------------------------------
    def apply(self, raw: str) -> str:
        if not raw:
            return "Biraz daha açık söyler misin?"

        text = " ".join(raw.strip().split())

        # ❌ İngilizce temizle
        bad_english = ["hello", "hi ", "how are you", "i am"]
        if any(b in text.lower() for b in bad_english):
            return "Türkçe devam edelim. Ne demek istedin?"

        # ❌ gereksiz girişleri sil
        starters = [
            "selam!",
            "merhaba!",
            "selam",
            "merhaba",
            "ben poodle",
            "ben de",
        ]

        lower = text.lower()
        for s in starters:
            if lower.startswith(s):
                text = text[len(s):].strip().capitalize()

        # ❌ robotik ifadeleri temizle
        replacements = {
            "gibi görünüyor": "",
            "gibi hissediyorum": "",
            "şu an": "",
        }

        for k, v in replacements.items():
            text = text.replace(k, v)

        # ❌ fazla uzun cevap kır
        parts = [p.strip() for p in text.split(".") if p.strip()]
        if len(parts) > 2:
            text = ". ".join(parts[:2])

        # ❌ boşluk düzelt
        text = text.strip()

        # ❌ çok kısa fallback
        if len(text) < 3:
            return "Biraz açar mısın?"

        return text
