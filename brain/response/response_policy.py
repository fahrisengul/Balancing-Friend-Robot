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
            "acknowledge",
            "followup",
            "conversation_start",
            "ask_question_back",
            "ask_topic",
            "open_topic",
        }

        if intent in template_intents:
            return Decision("template")

        skill_intents = {
            "ask_birthdate",
            "ask_age",
            "ask_day_date",
            "ask_time",
            "mute",
            "wake",
        }

        if intent in skill_intents:
            return Decision("skill")

        if intent in {"clarification_needed", "followup_repair", "low_confidence"}:
            return Decision("clarify", "Tam anlayamadım. Bir daha söyler misin?")

        return Decision("llm")

    def apply(self, raw: str) -> str:
        if not raw:
            return "Biraz daha açık söyler misin?"

        text = " ".join(raw.strip().split())
        lower = text.lower()

        banned = [
            "hello",
            "hi ",
            "how are you",
            "i am",
            "system prompt",
            "robotun adı poodle",
            "kisa dogal diyalog",
        ]
        if any(b in lower for b in banned):
            return "Bunu daha sade söyleyeyim. Ne demek istediğini biraz açar mısın?"

        starters = [
            "selam!",
            "merhaba!",
            "selam",
            "merhaba",
            "ben poodle",
            "ben de",
            "şu an",
        ]
        for s in starters:
            if lower.startswith(s):
                text = text[len(s):].strip()
                lower = text.lower()

        replacements = {
            "gibi görünüyor": "",
            "gibi hissediyorum": "",
            "şimdilik": "",
        }
        for old, new in replacements.items():
            text = text.replace(old, new).replace(old.capitalize(), new.capitalize())

        text = " ".join(text.split()).strip()
        text = self._tighten_education_style(text)

        parts = self._split_sentences(text)
        if len(parts) > 3:
            text = " ".join(parts[:3]).strip()

        if len(text) < 3:
            return "Biraz açar mısın?"

        if self.last_reply and self._is_similar(text, self.last_reply):
            text = self._diversify(text)

        self.last_reply = text
        return text

    def _tighten_education_style(self, text: str) -> str:
        t = text.strip()
        words = t.split()
        if len(words) > 40:
            t = " ".join(words[:40]).strip()
            if not t.endswith("."):
                t += "."

        replacements = {
            "yapmalısın": "yapabilirsin",
            "zorundasın": "istersen deneyebilirsin",
            "hemen bunu yap": "önce bunu deneyebilirsin",
            "başarısızsın": "zorlanıyor olabilirsin",
        }
        for old, new in replacements.items():
            t = t.replace(old, new).replace(old.capitalize(), new.capitalize())

        return " ".join(t.split()).strip()

    def _split_sentences(self, text: str):
        parts = []
        current = ""

        for ch in text:
            current += ch
            if ch in ".!?":
                parts.append(current.strip())
                current = ""

        if current:
            parts.append(current.strip())

        return parts

    def _is_similar(self, a: str, b: str) -> bool:
        a_tokens = set(a.lower().split())
        b_tokens = set(b.lower().split())
        if not a_tokens or not b_tokens:
            return False

        overlap = len(a_tokens & b_tokens) / max(len(a_tokens), 1)
        return overlap > 0.7

    def _diversify(self, text: str) -> str:
        fallback_variants = [
            "Bunu başka bir şekilde söyleyeyim.",
            "Şöyle düşünelim.",
            "Buna başka taraftan bakalım.",
        ]
        return fallback_variants[0]
