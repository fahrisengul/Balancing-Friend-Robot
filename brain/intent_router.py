import re


class IntentRouter:

    def detect(self, text: str) -> str:
        t = (text or "").lower().strip()

        # 🔹 greeting
        if any(x in t for x in ["selam", "merhaba", "hey"]):
            return "greeting"

        # 🔹 farewell
        if any(x in t for x in ["görüşürüz", "gorusuruz", "hoşça kal", "hosca kal", "bay", "bye"]):
            return "farewell"

        # 🔹 name
        if "adın ne" in t or "adin ne" in t:
            return "ask_name"

        # 🔹 identity
        if "sen kimsin" in t:
            return "ask_identity"

        # 🔹 status
        if "nasılsın" in t or "nasilsin" in t:
            return "ask_status"

        # 🔹 follow-up repair
        if any(x in t for x in [
            "sormuştum",
            "demek istemiştim",
            "yanlış söyledim",
            "tekrar soruyorum"
        ]):
            return "followup_repair"

        # 🔹 question detection
        if self._is_question(t):
            return "question"

        # 🔹 statement
        if len(t.split()) >= 2:
            return "statement"

        return "smalltalk_short"

    def _is_question(self, text: str) -> bool:
        question_words = [
            "ne", "neden", "nasıl", "nasil", "nerede", "ne zaman",
            "hangi", "kim", "kaç", "kac", "mi", "mı", "mu", "mü"
        ]

        return any(q in text for q in question_words)
