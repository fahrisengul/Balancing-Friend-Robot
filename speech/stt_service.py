import numpy as np


class STTService:
    def __init__(self, owner):
        self.owner = owner

    def process_speech(self, audio_int16: np.ndarray) -> str:
        """
        audio_int16: numpy array (int16 mono)
        """

        if audio_int16 is None or len(audio_int16) == 0:
            return ""

        try:
            # Whisper expects float32 [-1,1]
            audio_float = audio_int16.astype(np.float32) / 32768.0

            result = self.owner.stt_model.transcribe(
                audio_float,
                language=self.owner.lang,
                fp16=False
            )

            text = result.get("text", "").strip()
            return text

        except Exception as e:
            print(f">>> [STT ERROR] {type(e).__name__}: {e}")
            return ""
