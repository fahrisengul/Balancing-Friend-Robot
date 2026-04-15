import subprocess
import tempfile
import os
from memory.processing.system_params import SystemParams


class TTSService:

    def __init__(self, speech_engine=None):
        # speech_engine opsiyonel (backward compatibility)
        self.speech_engine = speech_engine

        self.config = SystemParams.get_audio_config()
        self.output_mode = self.config.get("output_mode", "system_default")
        self.output_name = self.config.get("output_name")

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
        # mevcut piper / tts pipeline'ın buraya bağlı olduğunu varsayıyorum
        # burada sadece placeholder gösteriyorum

        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        path = temp_file.name
        temp_file.close()

        # 🔴 SENİN mevcut TTS üretim kodun buraya gelecek
        # örnek:
        # piper_generate(text, path)

        return path

    def _play_audio(self, path: str):
        try:
            if self.output_mode == "system_default":
                subprocess.run(["afplay", path])

            elif self.output_mode == "macbook_builtin":
                print(">>> [TTS] MacBook hoparlör (system default fallback)")
                subprocess.run(["afplay", path])

            elif self.output_mode == "jabra_preferred":
                print(">>> [TTS] Jabra tercih edildi (OS routing gerekli)")
                subprocess.run(["afplay", path])

            else:
                print(">>> [TTS] Unknown mode, fallback")
                subprocess.run(["afplay", path])

        finally:
            try:
                os.remove(path)
            except Exception:
                pass

    def speak_now(self, text: str):
        self.speak(text)

    def rebuild_daily_metrics(self):
        return
