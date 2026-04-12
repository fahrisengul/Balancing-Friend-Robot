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
from collections import deque

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
    ):
        self.lang = lang
        self.input_samplerate = input_samplerate
        self.block_duration_ms = block_duration_ms
        self.block_size = int(self.input_samplerate * self.block_duration_ms / 1000)

        self.audio_queue = queue.Queue()
        self.command_queue = queue.Queue()
        self.tts_queue = queue.Queue()

        self._wake_thread = None
        self._wake_running = False
        self._busy = False
        self._last_tts_time = 0.0
        self._tts_cooldown_sec = 0.65

        self._tts_thread = threading.Thread(target=self._tts_worker, daemon=True)
        self._tts_thread.start()

        self._pending_phrase = ""
        self._pending_phrase_since = 0.0
        self._min_phrase_chars = 28
        self._max_phrase_wait_sec = 0.7

        self.wake_aliases = [
            "poodle",
            "pudıl",
            "pudle",
            "poodle robot",
            "hey poodle",
            "merhaba poodle",
            "puddle",
            "padıl",
            "padali",
            "padalı",
            "podıl",
            "podle",
            "pudıl robot",
            "hey puddle",
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

        print(">>> [SES] Offline STT + Wake Word + VAD + Piper TTS hazır.")

    # =========================================================
    # DIŞ DURUM KONTROLÜ
    # =========================================================
    def set_busy(self, value: bool):
        self._busy = value

    # =========================================================
    # AUDIO INPUT
    # =========================================================
    def _audio_callback(self, indata, frames, time_info, status):
        if status:
            print(f">>> [AUDIO STATUS] {status}")
        self.audio_queue.put(indata.copy())

    def _record_fixed(self, duration_sec):
        self.audio_queue = queue.Queue()

        with sd.InputStream(
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

        audio = np.concatenate(chunks, axis=0).flatten().astype(np.float32)
        return audio

    # =========================================================
    # NORMALIZATION / WAKE MATCH
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

    def _contains_wake_word(self, text: str) -> bool:
        normalized = self._normalize_text(text)
        if not normalized:
            return False

        for alias in self.wake_aliases:
            alias_n = self._normalize_text(alias)
            if alias_n in normalized:
                return True

        tokens = normalized.split()
        candidates = set(tokens)

        if len(tokens) >= 2:
            for i in range(len(tokens) - 1):
                candidates.add(tokens[i] + " " + tokens[i + 1])

        core_targets = [
            "poodle",
            "pudil",
            "pudle",
            "puddle",
            "podil",
            "padali",
        ]

        for cand in candidates:
            for target in core_targets:
                if self._similarity(cand, target) >= 0.72:
                    return True

        return False

    # =========================================================
    # TTS
    # =========================================================
    def speak(self, text: str):
        cleaned = self._clean_tts_text(text)
        if not cleaned:
            return

        now = time.time()

        # kısa ve yarım phrase ise biraz beklet
        if self._should_hold_phrase(cleaned):
            if not self._pending_phrase:
                self._pending_phrase = cleaned
                self._pending_phrase_since = now
                return

            merged = f"{self._pending_phrase} {cleaned}".strip()
            self._pending_phrase = self._clean_tts_text(merged)

            if (
                len(self._pending_phrase) >= self._min_phrase_chars
                or self._pending_phrase.endswith((".", "!", "?"))
                or (now - self._pending_phrase_since) >= self._max_phrase_wait_sec
            ):
                self.tts_queue.put(self._pending_phrase)
                self._pending_phrase = ""
                self._pending_phrase_since = 0.0

            return

        # pending varsa önce onunla birleştir
        if self._pending_phrase:
            combined = f"{self._pending_phrase} {cleaned}".strip()
            cleaned = self._clean_tts_text(combined)
            self._pending_phrase = ""
            self._pending_phrase_since = 0.0

        self.tts_queue.put(cleaned)

    def flush_pending_tts(self):
        if self._pending_phrase:
            text = self._clean_tts_text(self._pending_phrase)
            self._pending_phrase = ""
            self._pending_phrase_since = 0.0
            if text:
                self.tts_queue.put(text)

    def _should_hold_phrase(self, text: str) -> bool:
        if not text:
            return False

        if text.endswith((".", "!", "?")):
            return False

        if text.endswith(","):
            return True

        if len(text) < self._min_phrase_chars:
            return True

        if len(text.split()) < 5:
            return True

        return False

    def _clean_tts_text(self, text: str) -> str:
        text = (text or "").replace("\n", " ").strip()
        text = " ".join(text.split())

        if not text:
            return ""

        if text in {",", ".", "!", "?", ";", ":"}:
            return ""

        # tek kelimelik kırık parçaları okutma
        if len(text.split()) == 1 and not text.endswith((".", "!", "?")):
            return ""

        return text

    def _tts_worker(self):
        while True:
            text = self.tts_queue.get()
            if text is None:
                break

            try:
                # çok sık tts spam'ini azalt
                now = time.time()
                delta = now - self._last_tts_time
                if delta < self._tts_cooldown_sec:
                    time.sleep(self._tts_cooldown_sec - delta)

                self._speak_now(text)
                self._last_tts_time = time.time()

            except Exception as e:
                print(f">>> [TTS ERROR] {e}")

    def _speak_now(self, text: str):
        print(f"Poodle: {text}")

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_wav:
            wav_path = tmp_wav.name

        try:
            with wave.open(wav_path, "wb") as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(22050)

                audio = self.voice.synthesize(text)
                if isinstance(audio, bytes):
                    wav_file.writeframes(audio)
                else:
                    pcm_bytes = self._to_pcm16_bytes(audio)
                    wav_file.writeframes(pcm_bytes)

            self._play_wav(wav_path)

        finally:
            if os.path.exists(wav_path):
                try:
                    os.remove(wav_path)
                except Exception:
                    pass

    def _to_pcm16_bytes(self, audio) -> bytes:
        if isinstance(audio, np.ndarray):
            arr = np.clip(audio, -1.0, 1.0)
            arr = (arr * 32767).astype(np.int16)
            return arr.tobytes()

        if isinstance(audio, array.array):
            return audio.tobytes()

        if isinstance(audio, list):
            arr = np.array(audio, dtype=np.float32)
            arr = np.clip(arr, -1.0, 1.0)
            arr = (arr * 32767).astype(np.int16)
            return arr.tobytes()

        raise TypeError(f"Desteklenmeyen audio tipi: {type(audio)}")

    def _play_wav(self, wav_path: str):
        system = platform.system()

        if system == "Darwin":
            subprocess.run(["afplay", wav_path], check=False)
        elif system == "Linux":
            subprocess.run(["aplay", wav_path], check=False)
        else:
            data, sr = self._read_wav_numpy(wav_path)
            sd.play(data, sr)
            sd.wait()

    def _read_wav_numpy(self, wav_path: str):
        with wave.open(wav_path, "rb") as wf:
            sr = wf.getframerate()
            frames = wf.readframes(wf.getnframes())
            data = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32767.0
            return data, sr
