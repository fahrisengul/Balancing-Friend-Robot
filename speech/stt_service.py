import os
import wave
import tempfile


class STTService:
    def __init__(self, owner):
        self.owner = owner

    def process_speech(self, audio_int16):
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            with wave.open(tmp_path, "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(self.owner.sample_rate)
                wf.writeframes(audio_int16.tobytes())

            segments, _ = self.owner.stt_model.transcribe(tmp_path, language=self.owner.lang)
            text = " ".join([s.text for s in segments]).strip()

        finally:
            try:
                os.remove(tmp_path)
            except Exception:
                pass

        if not text or len(text) < 2:
            return

        self.owner.log_time(f">>> [STT] '{text}'")

        lowered = text.lower()

        if any(w in lowered for w in ["sus", "sessiz ol", "dur"]):
            self.owner._muted = True
            self.owner.log_time(">>> [MODE] Sessiz mod.")
            self.owner.event_queue.append({"type": "sleep"})
            return

        if self.owner._muted and any(w in lowered for w in ["uyan", "devam et", "konuşabilirsin", "hey"]):
            self.owner._muted = False
            self.owner.log_time(">>> [MODE] Aktif mod.")
            self.owner.event_queue.append({"type": "resumed"})
            return

        if not self.owner._muted:
            self.owner.event_queue.append({"type": "command", "text": text})
