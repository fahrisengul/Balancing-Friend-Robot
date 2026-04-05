import os
import wave
import array
import queue
import tempfile
import threading
import platform
import subprocess
import time
import re
import unicodedata
from difflib import SequenceMatcher

import numpy as np
import sounddevice as sd
import torch

from faster_whisper import WhisperModel
from piper.voice import PiperVoice
from silero_vad import load_silero_vad, get_speech_timestamps


class PoodleSpeech:
    def __init__(
        self,
        lang="tr",
        input_samplerate=16000,
        whisper_model_size="base",
        whisper_compute_type="int8",
        whisper_cpu_threads=4,
        block_duration_ms=200,
        input_device=None,   # ör: "FahriSengul Mikrofonu"
    ):
        self.lang = lang
        self.input_samplerate = input_samplerate
        self.block_duration_ms = block_duration_ms
        self.block_size = int(self.input_samplerate * self.block_duration_ms / 1000)

        self.audio_queue = queue.Queue()
        self.event_queue = queue.Queue()

        self._listener_thread = None
        self._listener_running = False
        self._busy = False
        self._muted = False
        self._last_tts_time = 0.0
        self._tts_cooldown_sec = 2.0
        self._audio_lock = threading.Lock()

        self._last_spoken_text = ""
        self._last_spoken_until = 0.0
        self._post_speak_ignore_sec = 4.5

        self.input_device = self._select_input_device(input_device)

        self.stop_aliases = [
            "sus",
            "sessiz ol",
            "konusma",
            "konuşma",
            "yeter",
            "tamam sus",
            "simdilik sus",
            "şimdilik sus",
            "artık sus",
            "kapa sesini",
        ]

        self.resume_aliases = [
            "hey",
            "hey poodle",
            "hey pudal",
            "hey puddle",
            "hey robot",
            "merhaba",
            "merhaba poodle",
        ]

        print(">>> Whisper modeli yükleniyor...")
        self.whisper = WhisperModel(
            whisper_model_size,
            device="cpu",
            compute_type=whisper_compute_type,
            cpu_threads=whisper_cpu_threads,
        )

        print(">>> Silero VAD yükleniyor...")
        self.vad_model = load_silero_vad()

        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.model_path = os.path.join(current_dir, "tr_TR-fahrettin-medium.onnx")

        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"Piper model bulunamadı: {self.model_path}")

        print(">>> Piper modeli yükleniyor...")
        self.voice = PiperVoice.load(self.model_path)

        print(">>> [SES] Doğal dinleme + STT + Piper TTS hazır.")

    # =========================================================
    # DEVICE
    # =========================================================
    def _select_input_device(self, preferred_name=None):
        devices = sd.query_devices()
        default_input, _ = sd.default.device

        chosen_index = None

        if preferred_name:
            pref = preferred_name.lower()
            for idx, dev in enumerate(devices):
                if dev["max_input_channels"] > 0 and pref in dev["name"].lower():
                    chosen_index = idx
                    break

        if chosen_index is None and default_input is not None and default_input >= 0:
            try:
                dev = devices[default_input]
                if dev["max_input_channels"] > 0:
                    chosen_index = default_input
            except Exception:
                pass

        if chosen_index is None:
            for idx, dev in enumerate(devices):
                if dev["max_input_channels"] > 0:
                    chosen_index = idx
                    break

        if chosen_index is None:
            raise RuntimeError("Hiç input audio device bulunamadı.")

        dev = devices[chosen_index]
        print(f">>> [MIC] Kullanılan input device: #{chosen_index} - {dev['name']}")
        return chosen_index

    def debug_list_input_devices(self):
        print(">>> [MIC DEBUG] Input cihazları:")
        for idx, dev in enumerate(sd.query_devices()):
            if dev["max_input_channels"] > 0:
                print(f"    #{idx}: {dev['name']} | in={dev['max_input_channels']}")

    # =========================================================
    # STATE
    # =========================================================
    def set_busy(self, value: bool):
        self._busy = value

    def is_muted(self):
        return self._muted

    # =========================================================
    # AUDIO
    # =========================================================
    def _audio_callback(self, indata, frames, time_info, status):
        if status:
            print(f">>> [AUDIO STATUS] {status}")
        self.audio_queue.put(indata.copy())

    def _record_fixed(self, duration_sec):
        self.audio_queue = queue.Queue()

        with self._audio_lock:
            with sd.InputStream(
                device=self.input_device,
                samplerate=self.input_samplerate,
                channels=1,
                dtype="float32",
                blocksize=self.block_size,
                callback=self._audio_callback,
            ):
                sd.sleep(int(duration_sec * 1000))

        chunks = []
        while not self.audio_queue.empty():
            chunks.append(self.audio_queue.get())

        if not chunks:
            return np.array([], dtype=np.float32)

        return np.concatenate(chunks, axis=0).flatten().astype(np.float32)

    # =========================================================
    # AUDIO PREP
    # =========================================================
    def _normalize_audio(self, audio_float32: np.ndarray) -> np.ndarray:
        if len(audio_float32) == 0:
            return audio_float32

        audio = audio_float32.astype(np.float32).copy()
        audio = audio - np.mean(audio)

        peak = np.max(np.abs(audio)) if len(audio) else 0.0
        rms = float(np.sqrt(np.mean(audio ** 2))) if len(audio) else 0.0
        print(f">>> [AUDIO DEBUG] peak={peak:.4f} rms={rms:.4f}")

        if peak > 0:
            gain = min(0.92 / peak, 10.0)
            audio = audio * gain

        return np.clip(audio, -1.0, 1.0).astype(np.float32)

    # =========================================================
    # TEXT NORMALIZATION
    # =========================================================
    def _normalize_text(self, text: str) -> str:
        text = text.lower().strip()
        text = unicodedata.normalize("NFKD", text)
        text = "".join(ch for ch in text if not unicodedata.combining(ch))
        text = re.sub(r"[^a-z0-9çğıöşü\s]", " ", text)
        text = re.sub(r"\s+", " ", text).strip()

        replacements = {
            "ı": "i",
            "ğ": "g",
            "ş": "s",
            "ç": "c",
            "ö": "o",
            "ü": "u",
        }
        for old, new in replacements.items():
            text = text.replace(old, new)

        return text

    def _similarity(self, a: str, b: str) -> float:
        return SequenceMatcher(None, a, b).ratio()

    def _contains_stop_command(self, text: str) -> bool:
        n = self._normalize_text(text)
        if not n:
            return False

        for alias in self.stop_aliases:
            if self._normalize_text(alias) in n:
                return True

        return False

    def _contains_resume_command(self, text: str) -> bool:
        n = self._normalize_text(text)
        if not n:
            return False

        for alias in self.resume_aliases:
            if self._normalize_text(alias) in n:
                return True

        if n == "hey":
            return True

        tokens = n.split()
        for token in tokens:
            if self._similarity(token, "hey") >= 0.8:
                return True

        return False

    def _is_too_short_or_weak_text(self, text: str) -> bool:
        n = self._normalize_text(text)
        if not n:
            return True

        tokens = [t for t in n.split() if t.strip()]
        if len(tokens) == 0:
            return True

        weak_tokens = {
            "aba", "baba", "he", "hey", "ya", "ee", "hmm", "tamam", "peki"
        }

        if len(tokens) == 1 and tokens[0] in weak_tokens:
            return True

        return False

    def _looks_like_echo_of_tts(self, text: str) -> bool:
        """
        Robotun kendi son konuşmasının mikrofondan geri dönmesini ayıklar.
        """
        if not text or not self._last_spoken_text:
            return False

        now = time.time()

        if now > self._last_spoken_until:
            return False

        heard = self._normalize_text(text)
        spoken = self._normalize_text(self._last_spoken_text)

        if not heard or not spoken:
            return False

        if heard in spoken and len(heard) >= 5:
            return True

        sim = self._similarity(heard, spoken)
        if sim >= 0.55:
            return True

        heard_tokens = set(heard.split())
        spoken_tokens = set(spoken.split())
        overlap = heard_tokens.intersection(spoken_tokens)

        if len(overlap) >= 2:
            return True

        return False

    # =========================================================
    # VAD
    # =========================================================
    def _detect_speech_regions(self, audio_float32):
        if len(audio_float32) == 0:
            return []

        audio_tensor = torch.from_numpy(audio_float32)
        return get_speech_timestamps(
            audio_tensor,
            self.vad_model,
            sampling_rate=self.input_samplerate,
            return_seconds=False,
        )

    def _has_speech(self, audio_float32, min_speech_ms=100):
        regions = self._detect_speech_regions(audio_float32)
        min_samples = int(self.input_samplerate * min_speech_ms / 1000)

        for region in regions:
            if (region["end"] - region["start"]) >= min_samples:
                return True
        return False

    # =========================================================
    # STT
    # =========================================================
    def _transcribe(self, audio_float32, beam_size=2):
        if len(audio_float32) == 0:
            return ""

        prepared = self._normalize_audio(audio_float32)

        segments, _ = self.whisper.transcribe(
            prepared,
            language=self.lang,
            beam_size=beam_size,
            vad_filter=False,
            condition_on_previous_text=False,
            initial_prompt="Türkçe konuşma. Robot asistan. Günlük konuşma. Hey. Sus.",
        )

        parts = []
        for segment in segments:
            if segment.text:
                parts.append(segment.text.strip())

        return " ".join(t for t in parts if t).strip()

    def listen_once(self, duration_sec=3.6):
        audio = self._record_fixed(duration_sec)

        if len(audio) == 0:
            return None

        if not self._has_speech(audio, min_speech_ms=100):
            return None

        text = self._transcribe(audio, beam_size=2)
        print(f">>> [STT DEBUG] transcript: {text}")

        if not text or not text.strip():
            return None

        text = text.lower().strip()

        if self._is_too_short_or_weak_text(text):
            print(">>> [FILTER] Çok kısa / zayıf transkript, yok sayıldı.")
            return None

        if self._looks_like_echo_of_tts(text):
            print(">>> [FILTER] TTS yankısı gibi görünüyor, yok sayıldı.")
            return None

        return text

    # =========================================================
    # AUTO LISTENER
    # =========================================================
    def _auto_loop(self):
        print("\n[DINLEME MODU] Robot doğal konuşma için arka planda dinliyor...")

        while self._listener_running:
            try:
                if self._busy:
                    time.sleep(0.15)
                    continue

                now = time.time()

                if now - self._last_tts_time < self._tts_cooldown_sec:
                    time.sleep(0.15)
                    continue

                if now < self._last_spoken_until:
                    time.sleep(0.15)
                    continue

                text = self.listen_once(duration_sec=3.6)
                if not text:
                    continue

                print(f">>> [AMBIENT TEXT] {text}")

                if self._muted:
                    if self._contains_resume_command(text):
                        self._muted = False
                        print(">>> [MODE] Sessiz mod kapandı, aktif dinleme geri geldi.")
                        self.event_queue.put({"type": "resumed", "text": None})
                    continue

                if self._contains_stop_command(text):
                    self._muted = True
                    print(">>> [MODE] Robot sessiz moda geçti.")
                    self.event_queue.put({"type": "sleep", "text": None})
                    continue

                self.event_queue.put({"type": "command", "text": text})

            except Exception as e:
                print(f">>> [AUTO LOOP HATASI] {type(e).__name__}: {e}")
                time.sleep(0.4)

    def start_auto_listener(self):
        if self._listener_thread and self._listener_thread.is_alive():
            return

        self._listener_running = True
        self._listener_thread = threading.Thread(target=self._auto_loop, daemon=True)
        self._listener_thread.start()

    def stop_auto_listener(self):
        self._listener_running = False

    def get_pending_event(self):
        try:
            return self.event_queue.get_nowait()
        except queue.Empty:
            return {"type": "none", "text": None}

    # =========================================================
    # TTS
    # =========================================================
    def _chunk_to_bytes(self, chunk):
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
                    return value.astype("int16").tobytes()

        try:
            seq = list(chunk)
            if seq and isinstance(seq[0], int):
                arr = array.array("h", seq)
                return arr.tobytes()
        except Exception:
            pass

        raise RuntimeError(
            f"AudioChunk çözümlenemedi. type={type(chunk)}, attrs={dir(chunk)}"
        )

    def _play_wav(self, wav_path):
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

    def speak(self, text):
        if not text:
            return

        print(f"Poodle: {text}")
        self._last_spoken_text = text
        temp_path = None

        try:
            self._busy = True

            sample_rate = self.voice.config.sample_rate
            pcm_buffer = bytearray()

            for chunk in self.voice.synthesize(text):
                chunk_bytes = self._chunk_to_bytes(chunk)
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

            self._play_wav(temp_path)

            self._last_tts_time = time.time()
            self._last_spoken_until = self._last_tts_time + self._post_speak_ignore_sec

        except Exception as e:
            print(f">>> [TTS HATASI] {type(e).__name__}: {e}")

        finally:
            self._busy = False
            if temp_path and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except Exception:
                    pass
