import json
import time


class AudioPipeline:
    def __init__(self, speech, brain, face=None):
        self.speech = speech
        self.brain = brain
        self.face = face

    def _set_face_state(self, state: str):
        if self.face is None:
            return

        try:
            self.face.set_state(state)
        except Exception:
            pass

    def _log_streaming_debug(
        self,
        intent: str,
        started_at: float,
        spoken_segments: list[str],
        flush_count: int,
        first_flush_ms: int | None,
    ):
        total_stream_ms = int((time.perf_counter() - started_at) * 1000)

        try:
            if hasattr(self.brain, "memory"):
                self.brain.memory.log_streaming_debug(
                    session_id=None,
                    intent=intent,
                    flush_count=flush_count,
                    first_flush_ms=first_flush_ms,
                    total_stream_ms=total_stream_ms,
                    total_chunks=len(spoken_segments),
                    spoken_segments_json=json.dumps(spoken_segments[:20], ensure_ascii=False),
                )
        except Exception as e:
            print(f">>> [LOG STREAMING ERROR] {e}")

    def _speak_text(self, text: str, intent: str):
        stream_started_at = time.perf_counter()
        spoken_segments: list[str] = []
        flush_count = 0
        first_flush_ms = None

        try:
            self._set_face_state("speaking")

            cleaned = (text or "").strip()
            if not cleaned:
                return

            self.speech.speak(cleaned)
            spoken_segments.append(cleaned)
            flush_count += 1

            if first_flush_ms is None:
                first_flush_ms = int((time.perf_counter() - stream_started_at) * 1000)

            self.speech.flush_pending_tts()

        finally:
            self._log_streaming_debug(
                intent=intent,
                started_at=stream_started_at,
                spoken_segments=spoken_segments,
                flush_count=flush_count,
                first_flush_ms=first_flush_ms,
            )
            self._set_face_state("idle")

    def _handle_command(self, text: str):
        self.speech.set_busy(True)

        try:
            self._set_face_state("thinking")
            result = self.brain.handle(text)
            reply = getattr(result, "reply_text", str(result))
            intent = getattr(result, "intent", "general")

            self._speak_text(reply, intent=intent)

        except Exception as e:
            print(f">>> [PIPELINE ERROR] {type(e).__name__}: {e}")
            self._set_face_state("error")
            self.speech.speak("Bir sorun yaşadım.")
            self.speech.flush_pending_tts()

        finally:
            self.speech.set_busy(False)
            self._set_face_state("idle")

    def _handle_sleep(self):
        self._set_face_state("idle")

    def _handle_resumed(self):
        self._set_face_state("idle")

    def process_event(self, event: dict):
        event_type = event.get("type", "none")

        if event_type == "none":
            return

        if event_type == "command":
            text = (event.get("text") or "").strip()
            if text:
                self._handle_command(text)
            return

        if event_type == "sleep":
            self._handle_sleep()
            return

        if event_type == "resumed":
            self._handle_resumed()
            return
