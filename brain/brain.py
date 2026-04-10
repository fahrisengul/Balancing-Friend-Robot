import random
from typing import Optional

from brain.intent_router import IntentRouter
from memory.memory_manager import MemoryManager


class PoodleBrain:
    def __init__(self):
        self.memory = MemoryManager()
        self.router = IntentRouter()

        patterns = self.memory.get_intent_patterns()
        self.router.load_patterns(patterns)

    def respond(self, text: str) -> str:
        intent, confidence = self.router.detect(text)

        if confidence < 0.4:
            return self._fallback()

        handler = getattr(self, f"_handle_{intent}", None)

        if handler:
            return handler(text)

        return self._template_or_fallback(intent)

    # -------------------------
    # CORE HANDLERS
    # -------------------------

    def _handle_greeting(self, text):
        return self._template_or_fallback("greeting")

    def _handle_identity(self, text):
        return "Ben Poodle. Seninle konuşan sakin bir robot arkadaşım."

    def _handle_ask_name(self, text):
        return "Benim adım Poodle."

    def _handle_smalltalk_howareyou(self, text):
        return "İyiyim. Sen nasılsın?"

    # -------------------------
    # SOCIAL FLOW
    # -------------------------

    def _handle_request_questioning(self, text):
        questions = [
            "Bugün seni en çok ne mutlu etti?",
            "Okulda en çok hangi dersi seviyorsun?",
            "Şu sıralar seni zorlayan bir şey var mı?",
        ]
        return random.choice(questions)

    def _handle_topic_suggestion(self, text):
        topics = [
            "İstersen oyunlar hakkında konuşabiliriz.",
            "İstersen okul hakkında konuşabiliriz.",
            "Bugün nasıl geçtiğini anlatmak ister misin?",
        ]
        return random.choice(topics)

    # -------------------------
    # EDUCATION COACH
    # -------------------------

    def _handle_exam_anxiety(self, text):
        return "Sınav seni biraz zorlamış gibi. Nerede zorlandığını birlikte bulabiliriz."

    def _handle_request_advice(self, text):
        if "5" in text:
            return (
                "1. Derin nefes al.\n"
                "2. Kısa bir mola ver.\n"
                "3. Kolay sorulardan başla.\n"
                "4. Kendine çok yüklenme.\n"
                "5. Küçük hedefler koy."
            )

        return "İstersen birlikte küçük bir plan yapabiliriz."

    def _handle_post_exam_reflection(self, text):
        return (
            "Bu çok normal. Bazen istediğimiz gibi gitmeyebilir.\n"
            "İstersen birlikte neyin zor geldiğini analiz edelim."
        )

    # -------------------------
    # TEMPLATE SYSTEM
    # -------------------------

    def _template_or_fallback(self, intent):
        template = self.memory.get_template(intent)

        if template:
            return template

        return self._fallback()

    def _fallback(self):
        return "Seni tam anlayamadım. Biraz daha açık söyler misin?"
