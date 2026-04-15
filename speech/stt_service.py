import os
import wave
import tempfile
import numpy as np


class STTService:
    def __init__(self, owner):
        self.owner = owner  # speech_engine referansı

    def process_speech(self, audio_int16):
        """
        audio_int16: numpy array (int16, mono, 16kHz)
        """

        if audio_int16 is None or len(audio_int16) == 0:
            return ""

        try:
            # -------------------------------------------------
            # 1. Audio normalize (garanti altına al)
            # -------------------------------------------------
            audio_int16 = np.array(audio_int16, dtype=np.int16)

            # -------------------------------------------------
            # 2. TEMP WAV oluştur
            # -------------------------------------------------
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
                tmp_path = tmp.name

            with wave.open(tmp_path, "wb") as wf:
                wf.setnchannels(1)       # mono
                wf.setsampwidth(2)       # int16 → 2 byte
                wf.setframerate(16000)   # 🔥 CRITICAL FIX
                wf.writeframes(audio_int16.tobytes())

            # -------------------------------------------------
            # 3. Whisper / STT çağrısı
            # -------------------------------------------------
            segments, _ = self.owner.stt_model.transcribe(
                tmp_path,
                language=self.owner.lang
            )

            # -------------------------------------------------
            # 4. Segment → text
            # -------------------------------------------------
            text = " ".join([seg.text for seg in segments]).strip()

            return text

        except Exception as e:
            print(f">>> [STT INTERNAL ERROR] {type(e).__name__}: {e}")
            return ""

        finally:
            # -------------------------------------------------
            # 5. TEMP CLEANUP
            # -------------------------------------------------
            try:
                if 'tmp_path' in locals() and os.path.exists(tmp_path):
                    os.remove(tmp_path)
            except Exception:
                pass
