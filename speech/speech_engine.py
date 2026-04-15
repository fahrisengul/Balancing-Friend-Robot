import threading
import time
import numpy as np

from speech.stt_service import STTService
from speech.tts_service import TTSService


class PoodleSpeech:
    def __init__(self, brain=None, lang="tr"):
        self.brain = brain
        self.lang = lang

        self.stt_model = self._load_stt_model()

        self.stt_service = STTService(owner=self)
        self.tts_service = TTSService()

        self.is_listening = True
        self.lock = threading.Lock()

        print(">>> [SES] Tüm sistemler hazır.")

    def _load_stt_model(self):
        import whisper
        return whisper.load_model("base")

    # ------------------------
    # LISTENER CONTROL
    # ------------------------

    def pause_listening(self):
        self.is_listening = False

    def resume_listening(self):
        self.is_listening = True

    # ------------------------
    # MAIN PIPELINE
    # ------------------------

    def process_audio(self, audio_int16):
        if not self.is_listening:
            return

        threading.Thread(
            target=self._process_speech,
            args=(audio_int16,),
            daemon=True
        ).start()

    def _process_speech(self, audio_int16):
        try:
            text = self.stt_service.process_speech(audio_int16)

            if not text:
                return

            print(f">>> [STT] '{text}'")

            # 🔹 Brain response
            if self.brain:
                reply = self.brain.ask_poodle(text)
            else:
                reply = "Anladım."

            print(f">>> [POODLE] {reply}")

            # 🔹 Speak
            self.pause_listening()
            self.tts_service.speak(reply)
            time.sleep(0.3)
            self.resume_listening()

        except Exception as e:
            print(f">>> [PIPELINE ERROR] {e}")
