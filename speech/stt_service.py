import os
import wave
import tempfile
import numpy as np


class STTService:
    def __init__(self, owner):
        self.owner = owner

    def process_speech(self, audio_int16, sample_rate=16000):
        if audio_int16 is None or len(audio_int16) == 0:
            return ""

        tmp_path = None

        try:
            audio_int16 = np.array(audio_int16, dtype=np.int16)

            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
                tmp_path = tmp.name

            with wave.open(tmp_path, "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(sample_rate)
                wf.writeframes(audio_int16.tobytes())

            segments, _ = self.owner.stt_model.transcribe(
                tmp_path,
                language=self.owner.lang,
                vad_filter=False,
            )

            text = " ".join(seg.text for seg in segments).strip()
            return text

        except Exception as e:
            print(f">>> [STT INTERNAL ERROR] {type(e).__name__}: {e}")
            return ""

        finally:
            try:
                if tmp_path and os.path.exists(tmp_path):
                    os.remove(tmp_path)
            except Exception:
                pass
