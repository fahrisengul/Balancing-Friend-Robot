import json
import threading
import time


class _StreamingBuffer:
    def __init__(
        self,
        min_flush_words: int = 14,
        max_flush_words: int = 30,
        min_chars_to_speak: int = 28,
        flush_timeout_sec: float = 1.1,
    ):
        self.min_flush_words = min_flush_words
        self.max_flush_words = max_flush_words
        self.min_chars_to_speak = min_chars_to_speak
        self.flush_timeout_sec = flush_timeout_sec

        self.buffer = ""
        self.last_update = time.monotonic()

    def add(self, chunk: str):
        if not chunk:
            return

        if self.buffer and not self.buffer.endswith((" ", "\n")) and not chunk.startswith((" ", ".", ",", "!", "?", ";", ":")):
            self.buffer += " "

        self.buffer += chunk
        self.last_update = time.monotonic()

    def has_content(self) -> bool:
        return bool(self.buffer.strip())

    def should_flush(self) -> bool:
        stripped = self.buffer.strip()
        if not stripped:
            return False

        words = stripped.split()

        # Tam cümle varsa
        if stripped.endswith((".", "!", "?")) and len(stripped) >= self.min_chars_to_speak:
            return True

        # Çok uzadıysa
        if len(words) >= self.max_flush_words:
            return True

        # Orta uzunluk + güvenli bağlaç
        if len(words) >= self.min_flush_words and self._has_soft_boundary(stripped):
            return True

        # Timeout
        if len(words) >= 6 and (time.monotonic() - self.last_update) >= self.flush_timeout_sec:
            return True

        return False

    def pop_ready_text(self) -> str:
        piece, remainder = self._extract_speakable_piece(self.buffer)
        self.buffer = remainder
        return piece

    def flush_all(self) -> str:
        text = self.buffer.strip()
        self.buffer = ""
        return text

    def _has_soft_boundary(self, text: str) -> bool:
        lower = text.lower()
        markers = [
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
            " yani ",
        ]
        return any(marker in lower for marker in markers)

    def _extract_speakable_piece(self, text: str):
        stripped = (text or "").strip()
        if not stripped:
            return "", ""

        # 1) Son tam cümleye kadar konuş
        last_sentence_end = max(
            stripped.rfind("."),
            stripped.rfind("!"),
            stripped.rfind("?"),
        )

        if last_sentence_end != -1 and last_sentence_end >= int(len(stripped) * 0.45):
            piece = stripped[: last_sentence_end + 1].strip()
            remainder = stripped[last_sentence_end + 1 :].strip()
            return piece, remainder

        # 2) Güvenli bağlaçta böl
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
            " yani ",
        ]

        lower = stripped.lower()
        best_idx = -1
        best_marker = ""

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

        # 3) Çok uzadıysa hepsini ver
        if len(stripped.split()) >= self.max_flush_words:
            return stripped, ""

        return "", stripped


class Orchestrator:
    def __init__(self, brain, speech, face):
        self.brain = brain
        self.speech = speech
        self.face = face

        self.state = "idle"
        self.running = True

        self._busy = False
        self._lock = threading.Lock()

        self.min_flush_words = 14
        self.max_flush_words = 30
        self.min_chars_to_speak = 28
        self.flush_timeout_sec = 1.1

    # =========================================================
    # LIFECYCLE
    # =========================================================
    def stop(self):
        self.running = False

    def set_state(self, state):
        self.state = state
        try:
            self.face.set_state(state)
        except Exception:
            pass

    # =========================================================
    # EVENT ENTRY
    # =========================================================
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
            text = (event.get("text") or "").strip()
            if text:
                self._start_async(self._process_command_stream, text)
            return

    # =========================================================
    # THREAD CONTROL
    # =========================================================
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

    # =========================================================
    # SIMPLE SPEAK
    # =========================================================
    def _speak_text(self, text):
        self.set_state("speaking")
        try:
            cleaned = self._clean_for_speech(text)
            if cleaned:
                flush_count += 1
                if first_flush_ms is None:
                    first_flush_ms = int((time.perf_counter() - stream_started_at) * 1000)
                spoken_segments.append(cleaned)
                self.speech.speak(cleaned)
                self.speech.flush_pending_tts()
        finally:
            self.set_state("idle")

    # =========================================================
    # STREAMING COMMAND FLOW
    # =========================================================
    def _process_command_stream(self, text):
        stream_started_at = time.perf_counter()
        first_flush_ms = None
        flush_count = 0
        total_chunks = 0
        spoken_segments = []
        inferred_intent = "general"
        buffer = _StreamingBuffer(
            min_flush_words=self.min_flush_words,
            max_flush_words=self.max_flush_words,
            min_chars_to_speak=self.min_chars_to_speak,
            flush_timeout_sec=self.flush_timeout_sec,
        )

        try:
            self.set_state("thinking")
            spoke_anything = False

            for item in self.brain.ask_poodle_stream(text):
                item_type = item.get("type")
                chunk_text = item.get("text", "")

                if item_type == "final":
                    final_text = self._clean_for_speech(chunk_text)
                    if final_text:
                        self.set_state("speaking")
                        self.speech.speak(final_text)
                        self.speech.flush_pending_tts()
                        spoke_anything = True
                    break

                if item_type == "chunk":
                    total_chunks += 1
                    buffer.add(chunk_text)

                    if buffer.should_flush():
                        piece = buffer.pop_ready_text()
                        cleaned = self._clean_for_speech(piece)

                        if cleaned:
                            self.set_state("speaking")
                            flush_count += 1
                            if first_flush_ms is None:
                                first_flush_ms = int((time.perf_counter() - stream_started_at) * 1000)
                            spoken_segments.append(cleaned)
                            self.speech.speak(cleaned)
                            self.speech.flush_pending_tts()
                            spoke_anything = True

                if item_type == "done":
                    remainder = buffer.flush_all()
                    cleaned = self._clean_for_speech(remainder or chunk_text)

                    if cleaned:
                        self.set_state("speaking")
                            flush_count += 1
                            if first_flush_ms is None:
                                first_flush_ms = int((time.perf_counter() - stream_started_at) * 1000)
                            spoken_segments.append(cleaned)
                        self.speech.speak(cleaned)
                        self.speech.flush_pending_tts()
                        spoke_anything = True
                    break

            # Stream bittikten sonra içerik kalmışsa son flush
            if buffer.has_content():
                remainder = buffer.flush_all()
                cleaned = self._clean_for_speech(remainder)
                if cleaned:
                    self.set_state("speaking")
                            flush_count += 1
                            if first_flush_ms is None:
                                first_flush_ms = int((time.perf_counter() - stream_started_at) * 1000)
                            spoken_segments.append(cleaned)
                    self.speech.speak(cleaned)
                    self.speech.flush_pending_tts()
                    spoke_anything = True

            if not spoke_anything:
                self.set_state("speaking")
                self.speech.speak("Şu an küçük bir sorun oluştu.")
                self.speech.flush_pending_tts()

        except Exception as e:
            print(f">>> [ORCHESTRATOR ERROR] {e}")
            self.set_state("error")
            self.speech.speak("Şu an küçük bir sorun oluştu.")
            self.speech.flush_pending_tts()
        finally:
            self.set_state("idle")

    # =========================================================
    # SPEECH CLEANING
    # =========================================================
    def _clean_for_speech(self, text: str) -> str:
        cleaned = (text or "").replace("\n", " ").replace("\r", " ").strip()
        cleaned = " ".join(cleaned.split())

        if not cleaned:
            return ""

        if cleaned in {",", ".", "!", "?", ";", ":"}:
            return ""

        # "Tanem," gibi tek başına kırık parça okutma
        if len(cleaned.split()) == 1 and cleaned.endswith(","):
            return ""

        # Çok kısa kırık phrase'leri engelle
        if len(cleaned) < self.min_chars_to_speak and not cleaned.endswith((".", "!", "?")):
            return ""

        return cleaned
