class Orchestrator:
    def __init__(self, brain, speech, face):
        self.brain = brain
        self.speech = speech
        self.face = face
        self.state = "idle"
        self.running = True

    def stop(self):
        self.running = False

    def set_state(self, state):
        self.state = state
        try:
            self.face.set_state(state)
        except Exception:
            pass

    def handle_event(self, event):
        if not self.running:
            return

        etype = event.get("type", "none")

        if etype == "none":
            return

        if etype == "sleep":
            self.set_state("muted")
            return

        if etype == "resumed":
            self.set_state("idle")
            return

        if etype == "clarify":
            self.set_state("speaking")
            self.speech.speak(event.get("text", "Seni tam anlayamadım."))
            self.set_state("idle")
            return

        if etype == "command":
            text = event.get("text", "").strip()
            if not text:
                return

            self.set_state("thinking")

            try:
                result = self.brain.handle_user_input(text)
                reply = result.reply_text

                self.set_state("speaking")
                self.speech.speak(reply)

            except Exception as e:
                print(f">>> [ORCHESTRATOR ERROR] {e}")
                self.set_state("error")
                self.speech.speak("Şu an küçük bir sorun oluştu.")

            finally:
                self.set_state("idle")
