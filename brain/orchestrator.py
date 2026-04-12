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

        # streaming / buffer ayarları
        self.min_flush_words = 16
        self.max_buffer_words = 28

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
            cleaned = self._clean_for_speech(text)
            if cleaned:
                self.speech.speak(cleaned)
        finally:
            self.set_state("idle")

    def _process_command_stream(self, text):
        try:
            self.set_state("thinking")

            buffer = ""
            streamed_any = False

            for item in self.brain.ask_poodle_stream(text):
                item_type = item.get("type")
                chunk_text = item.get("text", "")

                if item_type == "final":
                    cleaned = self._clean_for_speech(chunk_text)
                    if cleaned:
                        self.set_state("speaking")
                        self.speech.speak(cleaned)
                        streamed_any = True
                    break

                if item_type == "chunk":
                    buffer += chunk_text

                    if self._should_flush(buffer):
                        piece, remainder = self._extract_speakable_piece(buffer)

                        if piece:
                            cleaned = self._clean_for_speech(piece)
                            if cleaned:
                                self.set_state("speaking")
                                self.speech.speak(cleaned)
                                streamed_any = True

                        buffer = remainder

                if item_type == "done":
                    # done event'inde final text varsa onu kullan, yoksa buffer'ı konuş
                    final_text = self._clean_for_speech(chunk_text or buffer)
                    if final_text:
                        self.set_state("speaking")
                        self.speech.speak(final_text)
                        streamed_any = True
                    buffer = ""
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

    def _should_flush(self, text: str) -> bool:
        stripped = (text or "").strip()
        if not stripped:
            return False

        if stripped.endswith((".", "!", "?")):
            return True

        words = stripped.split()

        if len(words) >= self.max_buffer_words:
            return True

        if len(words) >= self.min_flush_words and self._has_soft_boundary(stripped):
            return True

        return False

    def _has_soft_boundary(self, text: str) -> bool:
        # Virgülde flush etmiyoruz
        soft_markers = [
            " çünkü ",
            " ama ",
            " fakat ",
            " ancak ",
            " sonra ",
            " ayrıca ",
            " böylece ",
            " örneğin ",
            " bu yüzden ",
            " bunun için ",
        ]
        lower = text.lower()
        return any(marker in lower for marker in soft_markers)

    def _extract_speakable_piece(self, text: str):
        stripped = (text or "").strip()
        if not stripped:
            return "", ""

        # 1. Tercih: son tam cümleye kadar konuş
        last_sentence_end = max(
            stripped.rfind("."),
            stripped.rfind("!"),
            stripped.rfind("?"),
        )

        if last_sentence_end != -1 and last_sentence_end >= int(len(stripped) * 0.45):
            piece = stripped[: last_sentence_end + 1].strip()
            remainder = stripped[last_sentence_end + 1 :].strip()
            return piece, remainder

        # 2. Tercih: güvenli yumuşak bağlaçlarda böl
        split_candidates = [
            " çünkü ",
            " ama ",
            " fakat ",
            " ancak ",
            " sonra ",
            " ayrıca ",
            " böylece ",
            " örneğin ",
            " bu yüzden ",
            " bunun için ",
        ]

        best_idx = -1
        best_marker = ""

        lower = stripped.lower()
        for marker in split_candidates:
            idx = lower.rfind(marker)
            if idx > best_idx and idx >= int(len(stripped) * 0.45):
                best_idx = idx
                best_marker = marker

        if best_idx != -1:
            cut_idx = best_idx + len(best_marker.strip())
            piece = stripped[:cut_idx].strip()
            remainder = stripped[cut_idx:].strip()
            return piece, remainder

        # 3. Son çare: buffer çok büyüdüyse hepsini konuş
        if len(stripped.split()) >= self.max_buffer_words:
            return stripped, ""

        return "", stripped

    def _clean_for_speech(self, text: str) -> str:
        cleaned = (text or "").replace("\n", " ").strip()
        cleaned = " ".join(cleaned.split())

        if cleaned in {",", ".", "!", "?", ";", ":"}:
            return ""

        if len(cleaned.split()) == 1 and cleaned.endswith(","):
            return ""

        return cleaned
