import os
import wave
import array
import tempfile
import platform
import subprocess
import time

import numpy as np


class TTSService:
    def __init__(self, owner):
        self.owner = owner

    def chunk_to_bytes(self, chunk) -> bytes:
        if chunk is None:
            return b""

        if isinstance(chunk, (bytes, bytearray)):
            return bytes(chunk)

        candidate_attrs = [
            "audio_int16_bytes",
            "audio_bytes",
            "pcm_bytes",
            "buffer",
            "audio",
            "samples",
        ]

        for attr in candidate_attrs:
            if hasattr(chunk, attr):
                value = getattr(chunk, attr)

                if value is None:
                    continue

                if isinstance(value, (bytes, bytearray)):
                    return bytes(value)

                if isinstance(value, (list, tuple, array.array)):
                    arr = array.array("h", value)
                    return arr.tobytes()

                if hasattr(value, "dtype") and hasattr(value, "tobytes"):
                    arr = np.asarray(value)
                    if arr.dtype != np.int16:
                        arr = arr.astype(np.int16)
                    return arr.tobytes()

        if hasattr(chunk, "dtype") and hasattr(chunk, "tobytes"):
            arr = np.asarray(chunk)
            if arr.dtype != np.int16:
                arr = arr.astype(np.int16)
            return arr.tobytes()

        try:
            seq = list(chunk)
            if seq and isinstance(seq[0], int):
                arr = array.array("h", seq)
                return arr.tobytes()
        except Exception:
            pass

        raise RuntimeError(f"AudioChunk çözümlenemedi. type={type(chunk)}")

    def play_wav(self, wav_path: str):
        system_name = platform.system()

        if system_name == "Darwin":
            cmd = ["/usr/bin/afplay", wav_path]
        elif system_name == "Linux":
            cmd = ["aplay", wav_path]
        else:
            raise RuntimeError(f"Desteklenmeyen işletim sistemi: {system_name}")

        result = subprocess.run(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
        )

        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or "Ses oynatma başarısız oldu.")

    def speak_now(self, text: str):
        if not text:
            return

        self.owner.log_time(f"Poodle: {text}")
        self.owner._busy = True

        temp_path = None
        try:
            now = time.time()
            delta = now - self.owner._last_tts_time
            if delta < self.owner._tts_cooldown_sec:
                time.sleep(self.owner._tts_cooldown_sec - delta)

            sample_rate = self.owner.voice.config.sample_rate
            pcm_buffer = bytearray()

            synth_result = self.owner.voice.synthesize(text)

            if synth_result is None:
                raise RuntimeError("Piper synthesize None döndü.")

            if isinstance(synth_result, np.ndarray):
                arr = synth_result
                if arr.dtype != np.int16:
                    arr = np.clip(arr, -1.0, 1.0)
                    arr = (arr * 32767.0).astype(np.int16)
                pcm_buffer.extend(arr.tobytes())
            elif isinstance(synth_result, (bytes, bytearray)):
                pcm_buffer.extend(bytes(synth_result))
            else:
                for chunk in synth_result:
                    chunk_bytes = self.chunk_to_bytes(chunk)
                    if chunk_bytes:
                        pcm_buffer.extend(chunk_bytes)

            if len(pcm_buffer) == 0:
                raise RuntimeError("Piper ses verisi üretmedi.")

            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                temp_path = tmp.name

            with wave.open(temp_path, "wb") as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(bytes(pcm_buffer))

            self.play_wav(temp_path)
            self.owner._last_tts_time = time.time()

        except Exception as e:
            self.owner.log_time(f">>> [TTS ERROR] {type(e).__name__}: {e}")

        finally:
            self.owner._busy = False
            if temp_path and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except Exception:
                    pass
