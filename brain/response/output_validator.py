import re
from typing import Optional


class OutputValidator:
    @classmethod
    def validate_llm_output(
        cls,
        reply: Optional[str],
        intent: str,
        mode: str,
        confidence: float,
    ) -> str:
        if not reply:
            return "Bunu bir kez daha söyler misin?"

        reply = reply.strip()
        if not reply:
            return "Bunu bir kez daha söyler misin?"

        if len(reply) > 420:
            reply = reply[:420].rstrip() + "..."

        low = reply.lower()

        forbidden_fragments = [
            "coming soon",
            "represent",
            "known edilir",
            "association",
            "happiness",
            "positive atmosphere",
            "artificial intelligence",
            "i am an ai",
        ]
        if any(x in low for x in forbidden_fragments):
            return cls.safe_fallback(intent, mode)

        if cls.looks_gibberish(reply):
            return cls.safe_fallback(intent, mode)

        if intent == "audio_check":
            return "Evet, seni duyuyorum."

        if intent == "greeting":
            return "Selam!"

        if intent == "thanks":
            return "Rica ederim."

        return reply

    @staticmethod
    def safe_fallback(intent: str, mode: str) -> str:
        if intent == "education_topics":
            return "İstersen bunu ders ders ve düzenli şekilde listeleyeyim."

        if intent == "concept_explanation":
            return "Bunu daha sade anlatayım. Hangi kısmını öğrenmek istiyorsun?"

        if intent == "exam_support":
            return "Bunu kısa ve uygulanabilir şekilde anlatayım."

        return "Bunu daha net söyleyeyim. İstersen bir kez daha sor."

    @staticmethod
    def looks_gibberish(text: str) -> bool:
        low = text.lower()

        weird_patterns = [
            "mu?", "mi?", "ouruzu", "represente", "known", "coming", "soon", "naw stress"
        ]
        weird_hits = sum(1 for p in weird_patterns if p in low)
        if weird_hits >= 2:
            return True

        if re.search(r"(.)\1\1\1", low):
            return True

        words = re.findall(r"\w+", low)
        if len(words) <= 2 and len(low) > 18:
            return True

        return False
