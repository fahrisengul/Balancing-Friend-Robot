class IntentRouter:
    def detect(self, text: str) -> str:
        raw = (text or "").strip()
        t = raw.lower()
        n = self._normalize(raw)

        if not n:
            return "clarification_needed"

        # greeting
        if any(x in n for x in ["selam", "merhaba", "hey poodle", "hey pudil", "hey puddle"]):
            # "hey poodle nasıl gidiyor" gibi birleşik ifadelerde status öncelikli olsun
            if any(q in n for q in ["nasil gidiyor", "nasilsin", "iyi misin"]):
                return "ask_status"
            return "greeting"

        # farewell
        if any(x in n for x in ["gorusuruz", "hosca kal", "bay bay", "bye"]):
            return "farewell"

        # thanks
        if any(x in n for x in ["tesekkur ederim", "tesekkurler", "sag ol", "sağ ol"]):
            return "thanks"

        # acknowledge
        if n in {"tamam", "peki", "olur", "anladim", "anladım"}:
            return "acknowledge"

        # name / identity
        if any(x in n for x in ["adin ne", "senin adin ne"]):
            return "ask_name"

        if "sen kimsin" in n:
            return "ask_identity"

        # status
        if any(x in n for x in ["nasilsin", "iyi misin", "nasil gidiyor", "nasil gidiy"]):
            return "ask_status"

        # deterministic skill intent'leri
        if "dogum gunum ne zaman" in n or "dogum gunu ne zaman" in n:
            return "ask_birthdate"

        if "kac yas" in n or "kaç yaş" in t:
            return "ask_age"

        if "saat kac" in n or "saat kaç" in t:
            return "ask_time"

        if "bugun gunlerden ne" in n or "bugün günlerden ne" in t:
            return "ask_day_date"

        if any(x in n for x in ["sus", "sessiz ol", "dur artik", "dur artık"]):
            return "mute"

        if n in {"hey", "uyan", "geri gel"}:
            return "wake"

        # follow-up repair / önceki konuşmayı düzeltme
        if any(x in n for x in [
            "sormustum", "sormuştum",
            "demek istemistim", "demek istemiştim",
            "yanlis soyledim", "yanlış söyledim",
            "tekrar soruyorum", "seni bunu sormustum"
        ]):
            return "followup_repair"

        # activity
        if any(x in n for x in [
            "bugun ne yaptin", "sen ne yaptin",
            "ne yaptin", "neler yaptin",
            "ne yapiyorsun", "neler yapiyorsun",
            "bugun neler yaptin"
        ]):
            return "ask_activity"

        # education / motivation
        if any(x in n for x in [
            "ders", "sinav", "motivasyon", "matematik", "fen", "ingilizce", "lgs", "tavsiye"
        ]):
            if "tavsiye" in n or "ne dersin" in n:
                return "question"
            return "education_help"

        # emotional
        if any(x in n for x in [
            "moralim bozuk", "uzgunum", "üzgünüm", "kotu hissediyorum", "kötü hissediyorum"
        ]):
            return "emotional_support"

        # doğal soru kalıpları
        if self._is_question(n):
            return "question"

        # 2+ kelimelik normal ifade
        if len(n.split()) >= 2:
            return "statement"

        return "smalltalk_short"

    def _is_question(self, text: str) -> bool:
        question_words = [
            "ne", "neden", "nasil", "nerede", "ne zaman",
            "hangi", "kim", "kac", "mi", "mı", "mu", "mü"
        ]
        return any(q in text for q in question_words)

    def _normalize(self, text: str) -> str:
        t = (text or "").lower().strip()
        t = (
            t.replace("ı", "i")
             .replace("ğ", "g")
             .replace("ş", "s")
             .replace("ç", "c")
             .replace("ö", "o")
             .replace("ü", "u")
        )
        return " ".join(t.split())
