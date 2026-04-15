from pathlib import Path
import os
import subprocess
import tempfile
import wave

from memory.processing.system_params import SystemParams
from piper.voice import PiperVoice


class TTSService:
    def __init__(self, speech_engine=None):
        self.speech_engine = speech_engine

        self.config = SystemParams.get_audio_config()
        self.output_mode = self.config.get("output_mode", "system_default")

        project_root = Path(__file__).resolve().parents[1]
        model_path = project_root / "models" / "tr_TR-fahrettin-medium.onnx"

        if not model_path.exists():
            raise FileNotFoundError(f"TTS model bulunamadı: {model_path}")

        self.voice = PiperVoice.load(str(model_path))

        print(f">>> [TTS INIT] mode={self.output_mode}")

    def speak(self, text: str):
        if not text:
            return

        try:
            wav_path = self._generate_wav(text)
            self._play_audio(wav_path)
        except Exception as e:
            print(f">>> [TTS ERROR] {e}")

    def speak_now(self, text: str):
        self.speak(text)

    def _generate_wav(self, text: str) -> str:
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        path = temp_file.name
        temp_file.close()

        with wave.open(path, "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(self.voice.config.sample_rate)

            for chunk in self.voice.synthesize(text):
                wav_file.writeframes(chunk.audio_int16_bytes)

        return path

    def _play_audio(self, path: str):
        try:
            subprocess.run(["afplay", path], check=False)
        finally:
            try:
                os.remove(path)
            except Exception:
                pass
