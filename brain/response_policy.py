from dataclasses import dataclass
from typing import Optional


@dataclass
class Decision:
    source: str
    clarify_text: Optional[str] = None


class ResponsePolicy:
    def __init__(self):
        self.last_reply = None

    def choose_source(self, text: str, intent: str) -> Decision:
        t = (text or "").strip().lower()

        if not t:
            return Decision("clarify", "Biraz daha açık söyler misin?")

        template_intents = {
            "greeting",
            "farewell",
            "ask_name",
            "ask_identity",
            "ask_status",
            "thanks",
            "conversation_start",
            "ask_question_back",
            "ask_topic",
            "open_topic",
            "ask_user_name",
            "user_name_define",
            "education_topics",
            "exam_support",
            "concept_explanation",
            "education_planning",
            "audio_check",
        }

        if intent in template_intents:
            return Decision("template")

        if len(t.split()) <= 2 and intent == "general":
            return Decision("clarify", "Son kısmı tam anlayamadım. Bir kez daha söyler misin?")

        return Decision("llm")

    def apply(self, raw: str) -> str:
        if not raw:
            return "Biraz daha açık söyler misin?"

        text = " ".join(raw.strip().split())
        lower = text.lower()

        if self._looks_like_persona_break(lower):
            return "Bunu daha sade söyleyeyim. Devam edelim mi?"

        text = self._strip_bad_openings(text)
        text = self._strip_meta_robotic(text)
        text = self._strip_garbage_terms(text)

        if not text:
            return "Bunu tam net duyamadım. İstersen bir kez daha söyle."

        text = self._limit_length(text)
        text = self._soften_style(text)
        text = self._force_child_friendly_style(text)

        if len(text.strip()) < 3:
            return "Biraz daha açık söyler misin?"

        if self.last_reply and self._is_similar(text, self.last_reply):
            text = self._diversify(text)

        self.last_reply = text
        return text.strip()

    def _looks_like_persona_break(self, lower: str) -> bool:
        banned = [
            "ben bir ai",
            "yapay zeka",
            "artificial intelligence",
            "i am an ai",
            "language model",
            "llm",
            "ai system",
            "ben bir sistemim",
            "as an ai",
            "sen poodle'sın",
            "sen poodlesin",
        ]
        return any(b in lower for b in banned)

    def _strip_bad_openings(self, text: str) -> str:
        bad_starts = [
            "Merhaba Tanem! ",
            "Merhaba! ",
            "Merhaba. ",
            "Selam Tanem! ",
            "Selam! ",
            "Selam. ",
            "Hey, ",
            "Tanem! ",
        ]

        result = text
        for bad in bad_starts:
            if result.startswith(bad):
                result = result[len(bad):].strip()

        return result

    def _strip_meta_robotic(self, text: str) -> str:
        replacements = {
            "Ben bir AI sistemiyim": "",
            "Ben bir yapay zeka sistemiyim": "",
            "Artificial Intelligence": "",
            "Size yardımcı olmaktan memnuniyet duyarım": "Yardımcı olmaya çalışırım",
            "Lütfen sorularınızı bildirin": "İstersen sorabilirsin",
            "gerçekten mi": "",
            "neden mi": "",
            "robot arkadaşın ve eğitim koçuymuşum": "robot arkadaşınım",
            "olacam": "olurum",
        }

        result = text
        for old, new in replacements.items():
            result = result.replace(old, new)
            result = result.replace(old.lower(), new)

        return " ".join(result.split()).strip()

    def _strip_garbage_terms(self, text: str) -> str:
        bad_terms = [
            "hız nav stressi",
            "naw stressi",
            "now see to see",
            "sinov",
            "hıznav",
            "naw",
        ]

        lowered = text.lower()

        if any(term in lowered for term in bad_terms):
            return ""

        return text

    def _limit_length(self, text: str) -> str:
        parts = self._split_sentences(text)
        if len(parts) > 2:
            text = " ".join(parts[:2]).strip()

        words = text.split()
        if len(words) > 22:
            text = " ".join(words[:22]).strip()
            if not text.endswith((".", "!", "?")):
                text += "."

        return text

    def _soften_style(self, text: str) -> str:
        replacements = {
            "zorundasın": "istersen deneyebilirsin",
            "yapmalısın": "yapabilirsin",
            "hemen yap": "önce bunu deneyebilirsin",
            "başarısız": "zorlanıyor",
            "çok yaygın bir durum": "olabilir",
        }

        result = text
        for old, new in replacements.items():
            result = result.replace(old, new)
            result = result.replace(old.capitalize(), new.capitalize())

        return result

    def _force_child_friendly_style(self, text: str) -> str:
        result = text.strip()

        if result in {"Tamam", "Peki"}:
            result += "."

        result = result.replace("??", "?").replace("!!", "!")
        result = result.replace("Hayır, hayır!", "Yok, şöyle diyeyim.")
        result = result.replace("Hayır,", "")
        result = result.replace("O zaman sana biraz bilgi vereyim.", "İstersen kısa anlatayım.")
        result = " ".join(result.split())

        return result

    def _split_sentences(self, text: str):
        parts = []
        current = ""

        for ch in text:
            current += ch
            if ch in ".!?":
                parts.append(current.strip())
                current = ""

        if current.strip():
            parts.append(current.strip())

        return parts

    def _is_similar(self, a: str, b: str) -> bool:
        a_tokens = set(a.lower().split())
        b_tokens = set(b.lower().split())

        if not a_tokens or not b_tokens:
            return False

        overlap = len(a_tokens & b_tokens) / max(len(a_tokens), 1)
        return overlap > 0.70

    def _diversify(self, text: str) -> str:
        fallbacks = [
            "Bunu daha kısa söyleyeyim.",
            "Şöyle diyeyim.",
            "Daha sade anlatayım.",
        ]
        return fallbacks[0]
