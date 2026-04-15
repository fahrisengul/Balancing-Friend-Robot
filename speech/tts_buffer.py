import time


class TTSBuffer:
    def __init__(self, owner):
        self.owner = owner
        print(">>> [TTS BUFFER] owner has pending?", hasattr(self.owner, "_pending_phrase"))

    def should_hold_phrase(self, text: str) -> bool:
        if not text:
            return False
        if text.endswith((".", "!", "?")):
            return False
        if text.endswith(","):
            return True
        if len(text) < self.owner._min_phrase_chars:
            return True
        if len(text.split()) < 5:
            return True
        return False

    def clean_tts_text(self, text: str) -> str:
        text = (text or "").replace("\n", " ").strip()
        text = " ".join(text.split())

        if not text:
            return ""

        if text in {",", ".", "!", "?", ";", ":"}:
            return ""

        if len(text.split()) == 1 and not text.endswith((".", "!", "?")):
            return ""

        return text

    def speak(self, text):
        cleaned = self.clean_tts_text(text)
        if not cleaned:
            return

        now = time.time()

        if self.should_hold_phrase(cleaned):
            if not self.owner._pending_phrase:
                self.owner._pending_phrase = cleaned
                self.owner._pending_phrase_since = now
                return

            merged = f"{self.owner._pending_phrase} {cleaned}".strip()
            self.owner._pending_phrase = self.clean_tts_text(merged)

            if (
                len(self.owner._pending_phrase) >= self.owner._min_phrase_chars
                or self.owner._pending_phrase.endswith((".", "!", "?"))
                or (now - self.owner._pending_phrase_since) >= self.owner._max_phrase_wait_sec
            ):
                self.owner._speak_now(self.owner._pending_phrase)
                self.owner._pending_phrase = ""
                self.owner._pending_phrase_since = 0.0
            return

        if self.owner._pending_phrase:
            combined = f"{self.owner._pending_phrase} {cleaned}".strip()
            cleaned = self.clean_tts_text(combined)
            self.owner._pending_phrase = ""
            self.owner._pending_phrase_since = 0.0

        self.owner._speak_now(cleaned)

    def flush_pending_tts(self):
        if self.owner._pending_phrase:
            text = self.clean_tts_text(self.owner._pending_phrase)
            self.owner._pending_phrase = ""
            self.owner._pending_phrase_since = 0.0
            if text:
                self.owner._speak_now(text)
