import subprocess
import tempfile
import os
from memory.processing.system_params import SystemParams
from piper import PiperVoice


class TTSService:

    def __init__(self, speech_engine=None):
        self.speech_engine = speech_engine

        self.config = SystemParams.get_audio_config()
        self.output_mode = self.config.get("output_mode", "system_default")
        self.output_name = self.config.get("output_name")

        # 🔥 Piper init (bir kere yüklenir)
        self.voice = PiperVoice.load(
            model_path="models/tr_TR-voice.onnx",   # senin model path
            config_path="models/tr_TR-voice.json"
        )

        print(f">>> [TTS INIT] mode={self.output_mode}, device={self.output_name}")

    def speak(self, text: str):
        if not text:
            return

        try:
            wav_path = self._generate_wav(text)
            self._play_audio(wav_path)
        except Exception as e:
            print(f">>> [TTS ERROR] {e}")

    def _generate_wav(self, text: str):
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        path = temp_file.name
        temp_file.close()

        # 🔥 GERÇEK SES ÜRETİMİ
        with open(path, "wb") as f:
            self.voice.synthesize(text, f)

        return path

    def _play_audio(self, path: str):
        try:
            if self.output_mode == "system_default":
                subprocess.run(["afplay", path])

            elif self.output_mode == "macbook_builtin":
                print(">>> [TTS] MacBook hoparlör")
                subprocess.run(["afplay", path])

            elif self.output_mode == "jabra_preferred":
                print(">>> [TTS] Jabra (system routing)")
                subprocess.run(["afplay", path])

            else:
                subprocess.run(["afplay", path])

        finally:
            try:
                os.remove(path)
            except Exception:
                pass

    def speak_now(self, text: str):
        self.speak(text)
