class IntentRouter:
    """
    Final sürüm:
    - kısa ve güvenli intent'leri erkenden yakalar
    - varyasyonları daha iyi destekler
    - follow-up cümlelerini bağlamlı işler
    - açık uçlu konuşmaları LLM'e bırakır
    """

    def detect(self, text: str, context=None) -> str:
        raw = (text or "").strip()
        t = raw.lower()
        normalized = self._normalize(raw)
        context = context or {}

        if not normalized:
            return "clarification_needed"

        # -----------------------------------------------------
        # Follow-up detection
        # -----------------------------------------------------
        followup_phrases = {
            "sonra",
            "e sonra",
            "ee sonra",
            "peki sonra",
            "neden",
            "neden oyle",
            "nasil",
            "nasil yani",
            "emin misin",
            "sonra ne oldu",
            "ne anladin",
            "ne dedin",
            "ne demek istedin",
            "yani",
            "ee",
        }
        if normalized in followup_phrases:
            return "followup"

        # Context varsa bazı kısa follow-up’ları daha rahat followup say
        if context.get("current_topic") and normalized in {"peki", "tamam peki"}:
            return "followup"

        # -----------------------------------------------------
        # Strong intents
        # -----------------------------------------------------
        if "kac yas" in normalized or "kaç yaş" in t:
            return "ask_age"

        if ("dogum" in normalized or "doğum" in t) and "ne zaman" in t:
            return "ask_birthdate"

        if "saat kac" in normalized or "saat kaç" in t:
            return "ask_time"

        if "bugun gunlerden ne" in normalized or "bugün günlerden ne" in t:
            return "ask_day_date"

        if "senin adin ne" in normalized or "adin ne" in normalized or "adın ne" in t:
            return "ask_name"

        if "sen kimsin" in normalized:
            return "ask_identity"

        # greeting + status birleşik hali
        if ("selam" in normalized or "merhaba" in normalized) and ("nasilsin" in normalized or "nasılsın" in t):
            return "ask_status"

        if "nasilsin" in normalized or "nasılsın" in t:
            return "ask_status"

        if "neler yapiyorsun" in normalized or "neler yapıyorsun" in t:
            return "ask_activity"

        if "ne yapiyorsun" in normalized or "ne yapıyorsun" in t:
            return "ask_activity"

        if "bugun ne yaptin" in normalized or "bugün ne yaptın" in t:
            return "ask_activity"

        if "sen ne yaptin" in normalized or "sen ne yaptın" in t:
            return "ask_activity"

        if "selam" in normalized or "merhaba" in normalized:
            return "greeting"

        if "tesekkur ederim" in normalized or "teşekkür ederim" in t:
            return "thanks"

        if normalized in {"tamam", "peki", "olur"}:
            return "acknowledge"

        if "sus" in normalized or "sessiz ol" in normalized or "dur" in normalized:
            return "mute"

        if normalized == "hey" or normalized.startswith("hey "):
            return "wake"

        # -----------------------------------------------------
        # Emotional / educational markers
        # -----------------------------------------------------
        emotional_markers = {
            "uzgunum",
            "moralim bozuk",
            "kotu hissediyorum",
            "yalniz hissediyorum",
            "canim sikkin",
        }
        if any(marker in normalized for marker in emotional_markers):
            return "emotional_support"

        educational_markers = {
            "matematik",
            "fen",
            "ingilizce",
            "lgs",
            "sinav",
            "ders",
            "netlerim",
            "test cozdum",
        }
        if any(marker in normalized for marker in educational_markers):
            return "education_help"

        # -----------------------------------------------------
        # Short natural utterances
        # -----------------------------------------------------
        if len(normalized.split()) <= 3:
            short_natural = {
                "selam",
                "merhaba",
                "nasilsin",
                "adin ne",
                "senin adin ne",
                "sen kimsin",
                "iyi misin",
                "ne anladin",
            }
            if normalized in short_natural:
                if "adin ne" in normalized:
                    return "ask_name"
                if "kimsin" in normalized:
                    return "ask_identity"
                if "nasilsin" in normalized or "iyi misin" in normalized:
                    return "ask_status"
                if normalized == "ne anladin":
                    return "followup"
                return "greeting"

            return "low_confidence"

        # -----------------------------------------------------
        # General fallback
        # -----------------------------------------------------
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
