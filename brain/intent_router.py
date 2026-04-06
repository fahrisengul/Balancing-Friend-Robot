class IntentRouter:

    def detect(self, text: str) -> str:
        t = text.lower()

        if "kaç yaş" in t:
            return "ask_age"

        if "doğum" in t and "ne zaman" in t:
            return "ask_birthdate"

        if "nasılsın" in t:
            return "ask_status"

        if "ne yaptın" in t:
            return "ask_activity"

        if "sus" in t:
            return "mute"

        if "hey" in t:
            return "wake"

        if len(t.split()) <= 2:
            return "low_confidence"

        return "general"
