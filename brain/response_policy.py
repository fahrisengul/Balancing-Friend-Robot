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

        if intent in {
            "question",
            "ask_activity",
            "education_help",
            "emotional_support",
            "general",
            "statement",
        }:
            return Decision("llm")

        return Decision("clarify", "Bunu tam anlayamadım. Biraz daha açık söyler misin?")

    def apply(self, raw: str) -> str:
        if not raw:
            return "Bunu biraz daha açık söyler misin?"

        text = " ".join(raw.strip().split())
        lowered = text.lower()

        hard_reject_patterns = [
            "ahaha",
            "hehe",
            "ooh",
            "oh dear",
            "hello",
            "how are you",
            "nice to meet you",
            "i'm doing well",
            "i am",
            "kullanıcı:",
            "system prompt",
            "robotun adı poodle",
            "robotun adi poodle",
            "kısa doğal diyalog",
            "kisa dogal diyalog",
        ]
        if any(p in lowered for p in hard_reject_patterns):
            return "Bunu daha sade söyleyeyim: biraz daha açık anlatır mısın?"

        leak_fragments = [
            "2013 yılında doğduğu",
            "ana kullanıcı profili",
            "okul çağındadır",
            "tanem ile konuşmaya hazırım",
            "tanem'le konuşmaya hazırım",
            "tanem ile çok keyifli sohbet etmek isterim",
            "tanem'le birlikte sohbet etmeye hazırım",
        ]
        for frag in leak_fragments:
            text = text.replace(frag, "").replace(frag.capitalize(), "")

        text = " ".join(text.split())

        english_markers = ["hello", "how are you", "nice to meet you", "what's new", "today?"]
        if any(m in lowered for m in english_markers):
            return "Türkçe devam edelim. Ne demek istediğini biraz daha açık söyler misin?"

        sentences = [s.strip() for s in text.split(".") if s.strip()]
        if len(sentences) > 2:
            text = ". ".join(sentences[:2]).strip()
            if not text.endswith("."):
                text += "."

        if len(text) < 3:
            return "Bunu biraz daha açık söyler misin?"

        return text
