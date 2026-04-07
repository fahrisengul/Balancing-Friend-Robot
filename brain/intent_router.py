class IntentRouter:
    """
    Amaç:
    - kısa ve güvenli intent'leri erkenden yakalamak
    - deterministic skill hattına yönlendirmek
    - açık uçlu konuşmaları LLM'e bırakmak
    """

    def detect(self, text: str) -> str:
        t = (text or "").lower().strip()

        if not t:
            return "clarification_needed"

        # -----------------------------------------------------
        # Exact / strong intents
        # -----------------------------------------------------
        if "kaç yaş" in t or "kac yas" in t:
            return "ask_age"

        if ("doğum" in t or "dogum" in t) and ("ne zaman" in t):
            return "ask_birthdate"

        if "saat kaç" in t or "saat kac" in t:
            return "ask_time"

        if "bugün günlerden ne" in t or "bugun gunlerden ne" in t:
            return "ask_day_date"

        if "adın ne" in t or "adin ne" in t:
            return "ask_name"

        if "sen kimsin" in t:
            return "ask_identity"

        if "nasılsın" in t or "nasilsin" in t:
            return "ask_status"

        if "bugün ne yaptın" in t or "bugun ne yaptin" in t:
            return "ask_activity"

        if "sen ne yaptın" in t or "sen ne yaptin" in t:
            return "ask_activity"

        if "selam" in t or "merhaba" in t:
            return "greeting"

        if "teşekkür ederim" in t or "tesekkur ederim" in t:
            return "thanks"

        if t in {"tamam", "peki", "olur"}:
            return "acknowledge"

        if "sus" in t or "sessiz ol" in t or "dur" in t:
            return "mute"

        if "hey" == t or t.startswith("hey "):
            return "wake"

        # -----------------------------------------------------
        # Short natural utterances
        # -----------------------------------------------------
        if len(t.split()) <= 2:
            short_natural = {
                "selam",
                "merhaba",
                "nasılsın",
                "nasilsin",
                "adın ne",
                "adin ne",
                "sen kimsin",
                "iyi misin",
            }
            if t in short_natural:
                if "ad" in t:
                    return "ask_name"
                if "kimsin" in t:
                    return "ask_identity"
                if "nasıl" in t or "nasilsin" in t:
                    return "ask_status"
                return "greeting"

            return "low_confidence"

        # -----------------------------------------------------
        # Follow-up / open talk
        # -----------------------------------------------------
        if t in {"emin misin", "neden", "neden öyle", "nasıl yani", "nasil yani"}:
            return "followup"

        emotional_markers = {
            "üzgünüm", "uzgunum", "moralim bozuk", "kötü hissediyorum", "kotu hissediyorum"
        }
        if any(marker in t for marker in emotional_markers):
            return "emotional_support"

        educational_markers = {
            "matematik", "fen", "ingilizce", "lgs", "sınav", "sinav", "ders"
        }
        if any(marker in t for marker in educational_markers):
            return "education_help"

        return "general"
