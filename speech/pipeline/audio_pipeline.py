class AudioPipeline:
    def __init__(self, speech, brain, face=None):
        self.speech = speech
        self.brain = brain
        self.face = face

    def _set_face_state(self, state: str):
        if self.face and hasattr(self.face, "set_state"):
            try:
                self.face.set_state(state)
            except Exception:
                pass

    def _safe_pause_listening(self):
        if hasattr(self.speech, "pause_listening"):
            try:
                self.speech.pause_listening()
            except Exception:
                pass

    def _safe_resume_listening(self):
        if hasattr(self.speech, "resume_listening"):
            try:
                self.speech.resume_listening()
            except Exception:
                pass

    def _speak_text(self, text, intent=None):
        if not text:
            return

        try:
            self._safe_pause_listening()
            self._set_face_state("speaking")
            self.speech.speak(text)
        finally:
            self._set_face_state("idle")
            self._safe_resume_listening()

    def _handle_command(self, text):
        if not text or not text.strip():
            return

        try:
            self._set_face_state("thinking")

            # 🔴 Eski hatalı çağrı:
            # reply = self.brain.respond(text)

            # ✅ Doğru çağrı:
            reply = self.brain.ask_poodle(text)

            print(f"[POODLE] {reply}")

            self._speak_text(reply)

        except Exception as e:
            print(f">>> [PIPELINE ERROR] {type(e).__name__}: {e}")
            self._speak_text("Bir sorun yaşadım.")

    def process_event(self, event):
        if not event:
            return

        event_type = event.get("type", "none")

        if event_type == "command":
            text = event.get("text", "")
            self._set_face_state("listening")
            self._handle_command(text)

        elif event_type == "sleep":
            self._set_face_state("sleep")

        elif event_type == "resumed":
            self._set_face_state("idle")
