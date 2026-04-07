class Orchestrator:

    def __init__(self, brain, speech, face):
        self.brain = brain
        self.speech = speech
        self.face = face

        self.state = "idle"

    def set_state(self, new_state):
        self.state = new_state
        self.face.set_state(new_state)

    def handle_event(self, event):

        etype = event.get("type")

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
            self.speech.speak(event["text"])
            self.set_state("idle")
            return

        if etype == "command":
            text = event.get("text")

            self.set_state("thinking")

            try:
                result = self.brain.handle_user_input(text)
                reply = result.reply_text

                self.set_state("speaking")
                self.speech.speak(reply)

            except Exception as e:
                print(f">>> [ORCHESTRATOR ERROR] {e}")
                self.speech.speak("Şu an küçük bir sorun oluştu.")

            finally:
                self.set_state("idle")
