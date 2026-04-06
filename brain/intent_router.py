class IntentRouter:
    def detect(self, text: str) -> str:
        t = text.lower()

        if "kaç yaş" in t or "kac yas" in t:
            return "ask_age"

        if "doğum" in t and "ne zaman" in t:
            return "ask_birthdate"

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

        if "sus" in t:
            return "mute"

        if "hey" in t:
            return "wake"

        if len(t.split()) <= 2:
            return "low_confidence"

        return "general"
