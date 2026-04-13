import os
import re
import time
import wave
import array
import queue
import tempfile
import threading
import platform
import subprocess
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
        input_device_index=None,
    ):
        self.lang = lang
        self.input_samplerate = input_samplerate
        self.block_duration_ms = block_duration_ms
        self.block_size = int(self.input_samplerate * self.block_duration_ms / 1000)

        self.input_device_index = input_device_index

        self.audio_queue = queue.Queue()
        self.event_queue = queue.Queue()
        self.tts_queue = queue.Queue()

        self._wake_thread = None
        self._wake_running = False
        self._busy = False
        self._muted = False
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
    # DEBUG TOOLS
    # =========================================================
    def debug_list_input_devices(self):
        print(">>> [MIC DEBUG] Cihaz Listesi:")
        try:
            devices = sd.query_devices()
            for i, dev in enumerate(devices):
                if dev["max_input_channels"] > 0:
                    print(f"    #{i}: {dev['name']}")
        except Exception as e:
            print(f">>> [MIC DEBUG ERROR] {e}")

    def select_default_input_device(self):
        try:
            devices = sd.query_devices()

            if self.input_device_index is not None and self.input_device_index >= 0:
                name = devices[self.input_device_index]["name"]
                print(f">>> [MIC ACTIVE] Manuel seçim: #{self.input_device_index} {name}")
                return self.input_device_index

            default_input = sd.default.device[0]
            if default_input is not None and default_input >= 0:
                self.input_device_index = default_input
                name = devices[default_input]["name"]
                print(f">>> [MIC ACTIVE] Otomatik seçim: #{default_input} {name}")
                return default_input

            for i, dev in enumerate(devices):
                if dev["max_input_channels"] > 0:
                    self.input_device_index = i
                    print(f">>> [MIC ACTIVE] Fallback seçim: #{i} {dev['name']}")
                    return i

        except Exception as e:
            print(f">>> [MIC SELECT ERROR] {e}")

        return None

    # =========================================================
    # STATE
    # =========================================================
    def is_muted(self):
        return self._muted

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

        stream_kwargs = {
            "samplerate": self.input_samplerate,
            "channels": 1,
            "dtype": "float32",
            "blocksize": self.block_size,
            "callback": self._audio_callback,
        }

        if self.input_device_index is not None and self.input_device_index >= 0:
            stream_kwargs["device"] = self.input_device_index

        with sd.InputStream(**stream_kwargs):
            sd.sleep(int(duration_sec * 1000))

        chunks = []
        while not self.audio_queue.empty():
            chunks.append(self.audio_queue.get())

        if not chunks:
            return np.array([], dtype=np.float32)

        audio = np.concatenate(chunks, axis=0).flatten().astype(np.float32)
        return audio

    # =========================================================
    # NORMALIZE / WAKE WORD
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

        core_targets = ["poodle", "pudil", "pudle", "puddle", "podil", "padali"]

        for cand in candidates:
            for target in core_targets:
                if self._similarity(cand, target) >= 0.72:
                    return True

        return False

    # =========================================================
    # VAD / STT
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

    def _has_speech(self, audio_float32, min_speech_ms=150):
        regions = self._detect_speech_regions(audio_float32)
        min_samples = int(self.input_samplerate * min_speech_ms / 1000)

        for region in regions:
            if (region["end"] - region["start"]) >= min_samples:
                return True
        return False

    def _transcribe(self, audio_float32, beam_size=1):
        if len(audio_float32) == 0:
            return ""

        segments, _ = self.whisper.transcribe(
            audio_float32,
            language=self.lang,
            beam_size=beam_size,
            vad_filter=False,
        )

        text_parts = []
        for segment in segments:
            if segment.text:
                text_parts.append(segment.text.strip())

        return " ".join(t for t in text_parts if t).strip()

    def transcribe_audio(self, audio: np.ndarray) -> str:
        if audio is None or len(audio) == 0:
            return ""
        return self._transcribe(audio, beam_size=1)

    def listen_command_vad(
        self,
        max_record_sec=8.0,
        silence_to_stop_ms=900,
        min_speech_ms=250,
        prebuffer_ms=600,
    ):
        print("\n[Dinleniyor...] Komutunu bekliyorum...")

        prebuffer_blocks = max(1, prebuffer_ms // self.block_duration_ms)
        silence_blocks_needed = max(1, silence_to_stop_ms // self.block_duration_ms)
        max_blocks = max(1, int(max_record_sec * 1000 / self.block_duration_ms))

        self.audio_queue = queue.Queue()
        prebuffer = []
        collected_blocks = []
        speech_started = False
        silence_counter = 0
        blocks_processed = 0

        stream_kwargs = {
            "samplerate": self.input_samplerate,
            "channels": 1,
            "dtype": "float32",
            "blocksize": self.block_size,
            "callback": self._audio_callback,
        }

        if self.input_device_index is not None and self.input_device_index >= 0:
            stream_kwargs["device"] = self.input_device_index

        with sd.InputStream(**stream_kwargs):
            while blocks_processed < max_blocks:
                try:
                    block = self.audio_queue.get(timeout=1.0)
                except queue.Empty:
                    break

                block = block.flatten().astype(np.float32)
                blocks_processed += 1

                if not speech_started:
                    prebuffer.append(block)
                    if len(prebuffer) > prebuffer_blocks:
                        prebuffer.pop(0)

                has_speech = self._has_speech(block, min_speech_ms=min_speech_ms)

                if has_speech and not speech_started:
                    print(">>> [AUDIO] Ses algılandı (VAD tetiklendi)...")
                    speech_started = True
                    collected_blocks.extend(prebuffer)
                    collected_blocks.append(block)
                    silence_counter = 0
                    continue

                if speech_started:
                    collected_blocks.append(block)

                    if has_speech:
                        silence_counter = 0
                    else:
                        silence_counter += 1

                    if silence_counter >= silence_blocks_needed:
                        print(">>> [VAD] Konuşma bitti, STT başlıyor.")
                        break

        if not collected_blocks:
            print(">>> [VAD] Geçerli konuşma bulunamadı.")
            return None

        audio = np.concatenate(collected_blocks, axis=0).astype(np.float32)
        text = self._transcribe(audio, beam_size=1)

        if not text:
            print(">>> [STT] Metin çıkarılamadı.")
            return None

        print(f">>> [STT] '{text}'")
        return text

    # =========================================================
    # AUTO LISTENER
    # =========================================================
    def start_auto_listener(self):
        if self._wake_running:
            return

        self._wake_running = True
        self._wake_thread = threading.Thread(target=self._auto_listen_loop, daemon=True)
        self._wake_thread.start()
        print("[DINLEME MODU] Arka plan dinlemesi aktif.")

    def stop_auto_listener(self):
        self._wake_running = False
        if self._wake_thread and self._wake_thread.is_alive():
            self._wake_thread.join(timeout=1.0)

    def get_pending_event(self):
        try:
            return self.event_queue.get_nowait()
        except queue.Empty:
            return {"type": "none"}

    def get_pending_command(self):
        evt = self.get_pending_event()
        if evt.get("type") == "command":
            return evt.get("text")
        return None

    def _auto_listen_loop(self):
        while self._wake_running:
            try:
                if self._busy:
                    time.sleep(0.05)
                    continue

                audio = self._record_fixed(2.0)

                if audio is None or len(audio) == 0:
                    continue

                text = self.transcribe_audio(audio)
                if not text:
                    continue

                print(f">>> [WAKE CHECK] {text}")
                lowered = text.lower().strip()

                if any(w in lowered for w in ["sus", "sessiz ol", "dur"]):
                    self._muted = True
                    self.event_queue.put({"type": "sleep"})
                    continue

                if self._muted and any(w in lowered for w in ["uyan", "devam et", "konuşabilirsin"]):
                    self._muted = False
                    self.event_queue.put({"type": "resumed"})
                    continue

                if self._muted:
                    continue

                if self._contains_wake_word(text):
                    print(">>> [WAKE WORD] Algılandı.")
                    self._busy = True

                    command = self.listen_command_vad(max_record_sec=6.0)

                    if command:
                        self.event_queue.put({"type": "command", "text": command})
                    else:
                        self.event_queue.put({"type": "clarify", "text": "Seni tam duyamadım."})

                    self._busy = False
                    continue

                if len(text.split()) >= 3:
                    self.event_queue.put({"type": "command", "text": text})

            except Exception as e:
                self._busy = False
                print(f">>> [AUTO LISTENER ERROR] {type(e).__name__}: {e}")
                time.sleep(0.2)

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

        raise RuntimeError(f"AudioChunk çözümlenemedi. type={type(chunk)}, attrs={dir(chunk)}")

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
        cleaned = self._clean_tts_text(text)
        if not cleaned:
            return

        now = time.time()

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

        if len(text.split()) == 1 and not text.endswith((".", "!", "?")):
            return ""

        return text

    def _tts_worker(self):
        while True:
            text = self.tts_queue.get()
            if text is None:
                break

            try:
                now = time.time()
                delta = now - self._last_tts_time
                if delta < self._tts_cooldown_sec:
                    time.sleep(self._tts_cooldown_sec - delta)

                self._speak_now(text)
                self._last_tts_time = time.time()

            except Exception as e:
                print(f">>> [TTS HATASI] {type(e).__name__}: {e}")

    def _speak_now(self, text: str):
        print(f"Poodle: {text}")

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

        finally:
            self._busy = False
            if temp_path and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except Exception:
                    pass
