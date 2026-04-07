class IntentRouter:
    """
    Amaç:
    - kısa ve güvenli intent'leri erkenden yakalamak
    - deterministic skill hattına yönlendirmek
    - follow-up cümlelerini ayrı ele almak
    - açık uçlu konuşmaları LLM'e bırakmak
    """

    def detect(self, text: str, context=None) -> str:
        t = (text or "").lower().strip()
        context = context or {}

        if not t:
            return "clarification_needed"

        normalized = self._normalize(t)

        # -----------------------------------------------------
        # Follow-up detection
        # -----------------------------------------------------
        followup_phrases = {
            "sonra",
            "e sonra",
            "peki sonra",
            "neden",
            "neden oyle",
            "nasil",
            "nasil yani",
            "emin misin",
            "sonra ne oldu",
            "ee",
            "ee sonra",
        }
        if normalized in followup_phrases:
            return "followup"

        # -----------------------------------------------------
        # Exact / strong intents
        # -----------------------------------------------------
        if "kaç yaş" in t or "kac yas" in normalized:
            return "ask_age"

        if ("doğum" in t or "dogum" in normalized) and ("ne zaman" in t or "ne zaman" in normalized):
            return "ask_birthdate"

        if "saat kaç" in t or "saat kac" in normalized:
            return "ask_time"

        if "bugün günlerden ne" in t or "bugun gunlerden ne" in normalized:
            return "ask_day_date"

        if "adın ne" in t or "adin ne" in normalized:
            return "ask_name"

        if "sen kimsin" in t:
            return "ask_identity"

        if "nasılsın" in t or "nasilsin" in normalized:
            return "ask_status"

        if "bugün ne yaptın" in t or "bugun ne yaptin" in normalized:
            return "ask_activity"

        if "sen ne yaptın" in t or "sen ne yaptin" in normalized:
            return "ask_activity"

        if "selam" in t or "merhaba" in t:
            return "greeting"

        if "teşekkür ederim" in t or "tesekkur ederim" in normalized:
            return "thanks"

        if normalized in {"tamam", "peki", "olur"}:
            return "acknowledge"

        if "sus" in t or "sessiz ol" in t or "dur" in t:
            return "mute"

        if normalized == "hey" or normalized.startswith("hey "):
            return "wake"

        # -----------------------------------------------------
        # Topic-aware weak follow-up handling
        # -----------------------------------------------------
        current_topic = context.get("current_topic")
        if current_topic and normalized in {"anladim", "devam", "sonra peki"}:
            return "followup"

        # -----------------------------------------------------
        # Short natural utterances
        # -----------------------------------------------------
        if len(normalized.split()) <= 2:
            short_natural = {
                "selam",
                "merhaba",
                "nasilsin",
                "adin ne",
                "sen kimsin",
                "iyi misin",
            }
            if normalized in short_natural:
                if "adin ne" == normalized:
                    return "ask_name"
                if "kimsin" in normalized:
                    return "ask_identity"
                if "nasilsin" in normalized:
                    return "ask_status"
                return "greeting"

            return "low_confidence"

        # -----------------------------------------------------
        # Emotional / educational markers
        # -----------------------------------------------------
        emotional_markers = {
            "üzgünüm", "uzgunum", "moralim bozuk", "kötü hissediyorum", "kotu hissediyorum"
        }
        if any(marker in t for marker in emotional_markers):
            return "emotional_support"

        educational_markers = {
            "matematik", "fen", "ingilizce", "lgs", "sınav", "sinav", "ders"
        }
        if any(marker in normalized for marker in educational_markers):
            return "education_help"

        return "general"

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
