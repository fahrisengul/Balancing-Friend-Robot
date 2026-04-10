class IntentRouter:

    def detect(self, text: str, context=None) -> str:
        raw = (text or "").strip()
        t = raw.lower()
        normalized = self._normalize(raw)
        context = context or {}

        if not normalized:
            return "clarification_needed"

        # -----------------------------------------------------
        # FOLLOW-UP (çok kritik fix)
        # -----------------------------------------------------
        followup_phrases = {
            "neden",
            "nasil",
            "peki",
            "yani",
            "ee",
            "ne anladin",
            "ne demek istedin",
            "sonra",
        }

        if normalized in followup_phrases:
            return "followup"

        if context.get("current_topic") and len(normalized.split()) <= 2:
            if normalized in {"peki", "tamam", "yani"}:
                return "followup"

        # -----------------------------------------------------
        # FAREWELL (eksikti → kritik)
        # -----------------------------------------------------
        if any(x in normalized for x in ["gorusuruz", "görüşürüz", "bay bay", "bye"]):
            return "farewell"

        # -----------------------------------------------------
        # GREETING / STATUS
        # -----------------------------------------------------
        if ("selam" in normalized or "merhaba" in normalized) and "nasilsin" in normalized:
            return "ask_status"

        if "nasilsin" in normalized:
            return "ask_status"

        if "selam" in normalized or "merhaba" in normalized:
            return "greeting"

        # -----------------------------------------------------
        # BASIC QUESTIONS
        # -----------------------------------------------------
        if "adin ne" in normalized:
            return "ask_name"

        if "kimsin" in normalized:
            return "ask_identity"

        if "ne yapiyorsun" in normalized or "neler yapiyorsun" in normalized:
            return "ask_activity"

        # -----------------------------------------------------
        # THANKS
        # -----------------------------------------------------
        if "tesekkur" in normalized:
            return "thanks"

        # -----------------------------------------------------
        # COMMANDS
        # -----------------------------------------------------
        if any(x in normalized for x in ["sus", "dur", "sessiz ol"]):
            return "mute"

        if normalized.startswith("hey"):
            return "wake"

        # -----------------------------------------------------
        # EDUCATION
        # -----------------------------------------------------
        if any(x in normalized for x in ["sinav", "ders", "matematik", "lgs"]):
            return "education_help"

        # -----------------------------------------------------
        # EMOTION
        # -----------------------------------------------------
        if any(x in normalized for x in ["uzgun", "moralim bozuk", "kotu hissediyorum"]):
            return "emotional_support"

        # -----------------------------------------------------
        # SHORT BUT VALID (kritik fix)
        # -----------------------------------------------------
        words = normalized.split()

        if len(words) <= 3:
            if "nasilsin" in normalized:
                return "ask_status"
            if "adin ne" in normalized:
                return "ask_name"
            if "kimsin" in normalized:
                return "ask_identity"
            if normalized in {"tamam", "peki", "olur"}:
                return "acknowledge"

            # artık direkt low_confidence demiyoruz
            return "general"

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
