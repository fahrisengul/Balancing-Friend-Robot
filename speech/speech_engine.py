import threading
import time
from datetime import datetime

from faster_whisper import WhisperModel
from speech.tts_buffer import TTSBuffer
from speech.stt_service import STTService


def ts():
    return datetime.now().strftime("[%H:%M:%S.%f]")[:-3]


class PoodleSpeech:
    def __init__(self):
        print(">>> Modeller yükleniyor (Whisper/VAD/Piper)...")

        # -------------------------
        # STATE
        # -------------------------
        self._speaking = False

        # -------------------------
        # STT MODEL
        # -------------------------
        from faster_whisper import WhisperModel

        print(">>> [STT MODEL] yükleniyor...")
        self.stt_model = WhisperModel("base", compute_type="int8")
        print(">>> [STT MODEL] faster_whisper hazır")

        # -------------------------
        # TTS ENGINE (GARANTİ)
        # -------------------------
        import pyttsx3

        self._engine = pyttsx3.init()
        self._engine.setProperty("rate", 180)

        # -------------------------
        # SERVICES
        # -------------------------
        from speech.stt_service import STTService
        from speech.tts_buffer import TTSBuffer

        self.stt_service = STTService(self)
        self._tts_buffer = TTSBuffer(self)

        print(">>> [SES] Tüm sistemler hazır.")

    # =========================================================
    # PUBLIC SPEAK
    # =========================================================
    def speak(self, text):
        print(">>> [SPEAK CALL]")
        print(f"Poodle: {text}")

        self._tts_buffer.speak(text)

    # =========================================================
    # INTERNAL SPEAK (BUFFER ÇAĞIRIR)
    # =========================================================
    def _speak_now(self, text):
        try:
            self._speaking = True

            print(">>> [TTS START]")

            self._engine.say(text)
            self._engine.runAndWait()

            print(">>> [TTS END]")

        except Exception as e:
            print(f">>> [TTS ERROR] {e}")

        finally:
            self._speaking = False
