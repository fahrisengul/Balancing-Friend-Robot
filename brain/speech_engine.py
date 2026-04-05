import os
import wave
import queue
import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel
from piper.voice import PiperVoice
import subprocess


class PoodleSpeech:
    def __init__(self, lang="tr"):
        self.lang = lang

        # ===== STT (Whisper) =====
        print(">>> Whisper modeli yükleniyor...")
        self.whisper = WhisperModel(
            "base",   # Pi için: tiny / base önerilir
            compute_type="int8"  # CPU optimizasyon
        )

        # ===== TTS (Piper) =====
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.model_path = os.path.join(current_dir, "tr_TR-fahrettin-medium.onnx")

        print(">>> Piper modeli yükleniyor...")
        self.voice = PiperVoice.load(self.model_path)

        # ===== Audio Queue =====
        self.audio_queue = queue.Queue()

        print(">>> [SES] Sistem hazır (Offline STT + TTS)")

    # ============================
    # 🎤 AUDIO RECORD
    # ============================
    def _audio_callback(self, indata, frames, time, status):
        if status:
            print(status)
        self.audio_queue.put(indata.copy())

    def record_audio(self, duration=4, samplerate=16000):
        print("\n[Dinleniyor...]")

        self.audio_queue = queue.Queue()

        with sd.InputStream(
            samplerate=samplerate,
            channels=1,
            callback=self._audio_callback
        ):
            sd.sleep(duration * 1000)

        audio_data = []
        while not self.audio_queue.empty():
            audio_data.append(self.audio_queue.get())

        audio = np.concatenate(audio_data, axis=0)
        return audio.flatten()

    # ============================
    # 🧠 STT (Whisper)
    # ============================
    def listen(self):
        try:
            audio = self.record_audio()

            segments, _ = self.whisper.transcribe(
                audio,
                language=self.lang,
                beam_size=1
            )

            text = ""
            for segment in segments:
                text += segment.text

            text = text.strip()

            if text:
                print(f"Tanem: {text}")
                return text.lower()

            return None

        except Exception as e:
            print(f">>> [STT HATASI] {e}")
            return None

    # ============================
    # 🔊 TTS (Piper - FIXED)
    # ============================
    def _chunk_to_bytes(self, chunk):
        import array

        if isinstance(chunk, (bytes, bytearray)):
            return bytes(chunk)

        for attr in ["audio", "samples", "pcm"]:
            if hasattr(chunk, attr):
                value = getattr(chunk, attr)

                if isinstance(value, (bytes, bytearray)):
                    return bytes(value)

                if isinstance(value, (list, tuple)):
                    return array.array("h", value).tobytes()

                if hasattr(value, "tobytes"):
                    return value.astype("int16").tobytes()

        raise RuntimeError("AudioChunk parse edilemedi")

    def speak(self, text):
        if not text:
            return

        print(f"Poodle: {text}")

        filename = "poodle_voice.wav"

        try:
            if os.path.exists(filename):
                os.remove(filename)

            sample_rate = self.voice.config.sample_rate
            pcm_buffer = bytearray()

            for chunk in self.voice.synthesize(text):
                pcm_buffer.extend(self._chunk_to_bytes(chunk))

            with wave.open(filename, "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(sample_rate)
                wf.writeframes(pcm_buffer)

            subprocess.run(
                ["/usr/bin/afplay", filename],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )

        except Exception as e:
            print(f">>> [TTS HATASI] {e}")

        finally:
            if os.path.exists(filename):
                os.remove(filename)
