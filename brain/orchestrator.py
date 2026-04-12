import threading


class Orchestrator:
    def __init__(self, brain, speech, face):
        self.brain = brain
        self.speech = speech
        self.face = face
        self.state = "idle"
        self.running = True
        self._busy = False
        self._lock = threading.Lock()

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
            self._start_async(self._speak_text, event.get("text", "Seni tam anlayamadım."))
            return

        if etype == "command":
            text = event.get("text", "").strip()
            if text:
                self._start_async(self._process_command_stream, text)
            return

    def _start_async(self, fn, *args):
        with self._lock:
            if self._busy:
                return
            self._busy = True

        thread = threading.Thread(target=self._run_async, args=(fn, *args), daemon=True)
        thread.start()

    def _run_async(self, fn, *args):
        try:
            fn(*args)
        finally:
            with self._lock:
                self._busy = False

    def _speak_text(self, text):
        self.set_state("speaking")
        try:
            self.speech.speak(text)
        finally:
            self.set_state("idle")

    def _process_command_stream(self, text):
        try:
            self.set_state("thinking")
            buffer = []
            streamed_any = False

            for item in self.brain.ask_poodle_stream(text):
                item_type = item.get("type")
                chunk_text = item.get("text", "")

                if item_type == "final":
                    self.set_state("speaking")
                    self.speech.speak(chunk_text)
                    streamed_any = True
                    break

                if item_type == "chunk":
                    buffer.append(chunk_text)

                    current = "".join(buffer).strip()
                    if self._should_flush(current):
                        self.set_state("speaking")
                        self.speech.speak(current)
                        buffer.clear()
                        streamed_any = True

                if item_type == "done":
                    final_text = "".join(buffer).strip()
                    if final_text:
                        self.set_state("speaking")
                        self.speech.speak(final_text)
                        buffer.clear()
                        streamed_any = True
                    break

            if not streamed_any:
                self.set_state("speaking")
                self.speech.speak("Şu an küçük bir sorun oluştu.")

        except Exception as e:
            print(f">>> [ORCHESTRATOR ERROR] {e}")
            self.set_state("error")
            self.speech.speak("Şu an küçük bir sorun oluştu.")
        finally:
            self.set_state("idle")

    def _should_flush(self, text):
        if not text:
            return False

        if text.endswith((".", "!", "?", ",", ";", ":")):
            return True

        return len(text.split()) >= 7
