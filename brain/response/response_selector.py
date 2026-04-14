from typing import Optional


class ResponseSelector:
    @staticmethod
    def select_llm_mode(
        intent: str,
        mode: str,
        confidence: float,
        selected_chunks: Optional[list] = None,
    ) -> str:
        selected_chunks = selected_chunks or []

        if intent in {"ask_name", "ask_identity", "audio_check", "thanks", "greeting", "farewell", "ask_status"}:
            return "deterministic"

        if intent in {"concept_explanation", "exam_support", "follow_up"}:
            return "deep"

        if intent == "education_topics":
            if confidence >= 0.60 or len(selected_chunks) >= 2:
                return "deep"
            return "balanced"

        if mode == "education":
            if confidence >= 0.70:
                return "deep"
            return "balanced"

        if confidence >= 0.75:
            return "deep"

        return "balanced"

    @staticmethod
    def try_fast_track(memory, text: str, intent: str, mode: str) -> Optional[str]:
        hard_intents = {"greeting", "ask_name", "ask_identity", "audio_check", "thanks", "farewell", "ask_status"}

        if intent in hard_intents:
            answer = memory.search_fast_answer(text, intent=intent)
            if answer:
                return answer

        if mode == "education" and intent == "education_topics":
            answer = memory.search_fast_answer(text, intent=intent)
            if answer:
                return answer

        return None

    @staticmethod
    def direct_reply(text: str, intent: str) -> Optional[str]:
        if intent == "conversation_start":
            return "Tamam. Ne hakkında konuşalım?"
        return None

    @staticmethod
    def get_template(memory, intent: str) -> Optional[str]:
        try:
            return memory.get_template(intent_name=intent)
        except Exception:
            return None
