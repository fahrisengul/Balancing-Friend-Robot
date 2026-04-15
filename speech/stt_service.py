import os
import wave
import tempfile
import traceback
import numpy as np


class STTService:
    def __init__(self, owner):
        self.owner = owner

    def process_speech(self, audio_int16, sample_rate=16000):
        print(">>> [STT SERVICE] process_speech entered")

        if audio_int16 is None or len(audio_int16) == 0:
            print(">>> [STT SERVICE] empty audio")
            return ""

        tmp_path = None

        try:
            audio_int16 = np.array(audio_int16, dtype=np.int16)
            print(f">>> [STT SERVICE] audio samples={len(audio_int16)} sample_rate={sample_rate}")

            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
                tmp_path = tmp.name

            print(f">>> [STT SERVICE] temp wav path={tmp_path}")

            with wave.open(tmp_path, "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(sample_rate)
                wf.writeframes(audio_int16.tobytes())

            print(">>> [STT SERVICE] wav written, calling faster_whisper...")

            segments, info = self.owner.stt_model.transcribe(
                tmp_path,
                language=self.owner.lang,
                vad_filter=False,
            )

            print(f">>> [STT SERVICE] transcribe returned info={info}")

            text_parts = []
            for seg in segments:
                print(f">>> [STT SEG] start={seg.start:.2f} end={seg.end:.2f} text={seg.text!r}")
                text_parts.append(seg.text)

            text = " ".join(text_parts).strip()
            print(f">>> [STT SERVICE] final text={text!r}")

            return text

        except Exception as e:
            print(f">>> [STT INTERNAL ERROR] {type(e).__name__}: {e}")
            traceback.print_exc()
            return ""

        finally:
            try:
                if tmp_path and os.path.exists(tmp_path):
                    os.remove(tmp_path)
                    print(">>> [STT SERVICE] temp wav removed")
            except Exception as e:
                print(f">>> [STT CLEANUP ERROR] {type(e).__name__}: {e}")
