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
        input_device=None,          # örn: "MacBook Pro Mikrofonu"
    ):
        self.lang = lang
        self.input_samplerate = input_samplerate
        self.block_duration_ms = block_duration_ms
        self.block_size = int(self.input_samplerate * self.block_duration_ms / 1000)

        self.audio_queue = queue.Queue()
        self.command_queue = queue.Queue()

        self._wake_thread = None
        self._wake_running = False
        self._busy = False
        self._last_tts_time = 0.0
        self._tts_cooldown_sec = 1.6
        self._audio_lock = threading.Lock()

        self.input_device = self._select_input_device(input_device)

        self.wake_aliases = [
            "poodle",
            "hey poodle",
            "merhaba poodle",
            "poodle robot",
            "pudle",
            "pudil",
            "puddle",
            "podil",
            "podle",
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
    # DEVICE SELECTION
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

        audio = np.concatenate(chunks, axis=0).flatten().astype(np.float32)
        return audio

    def _record_blocks_until(
        self,
        start_timeout_sec,
        max_record_sec,
        silence_to_stop_ms,
        min_speech_ms,
        prebuffer_ms,
    ):
        prebuffer_blocks = max(1, prebuffer_ms // self.block_duration_ms)
        silence_blocks_needed = max(1, silence_to_stop_ms // self.block_duration_ms)
        start_timeout_blocks = max(1, int(start_timeout_sec * 1000 / self.block_duration_ms))
        max_blocks_after_start = max(1, int(max_record_sec * 1000 / self.block_duration_ms))

        self.audio_queue = queue.Queue()
        prebuffer = deque(maxlen=prebuffer_blocks)

        collected_blocks = []
        speech_started = False
        silence_counter = 0
        start_wait_blocks = 0
        blocks_after_start = 0

        with self._audio_lock:
            with sd.InputStream(
                device=self.input_device,
                samplerate=self.input_samplerate,
                channels=1,
                dtype="float32",
                blocksize=self.block_size,
                callback=self._audio_callback,
            ):
                while True:
                    block = self.audio_queue.get()
                    block = block.flatten().astype(np.float32)

                    if not speech_started:
                        prebuffer.append(block)
                        start_wait_blocks += 1

                        block_has_speech = self._has_speech(block, min_speech_ms=min_speech_ms)
                        if block_has_speech:
                            speech_started = True
                            collected_blocks.extend(list(prebuffer))
                            collected_blocks.append(block)
                            silence_counter = 0
                            blocks_after_start = 1
                        elif start_wait_blocks >= start_timeout_blocks:
                            return None

                        continue

                    collected_blocks.append(block)
                    blocks_after_start += 1

                    block_has_speech = self._has_speech(block, min_speech_ms=min_speech_ms)

                    if block_has_speech:
                        silence_counter = 0
                    else:
                        silence_counter += 1

                    if silence_counter >= silence_blocks_needed:
                        break

                    if blocks_after_start >= max_blocks_after_start:
                        break

        if not collected_blocks:
            return None

        return np.concatenate(collected_blocks).astype(np.float32)

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
            target_peak = 0.92
            gain = min(target_peak / peak, 10.0)
            audio = audio * gain

        audio = np.clip(audio, -1.0, 1.0)
        return audio.astype(np.float32)

    # =========================================================
    # TEXT NORMALIZATION / WAKE MATCH
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
        if not tokens:
            return False

        candidates = set(tokens)
        if len(tokens) >= 2:
            for i in range(len(tokens) - 1):
                candidates.add(tokens[i] + " " + tokens[i + 1])

        core_targets = ["poodle", "pudle", "pudil", "puddle", "podil", "podle"]

        for cand in candidates:
            cand_clean = cand.strip()
            if len(cand_clean) < 5:
                continue

            for target in core_targets:
                if self._similarity(cand_clean, target) >= 0.84:
                    return True

                if cand_clean.startswith("hey ") or cand_clean.startswith("merhaba "):
                    tail = cand_clean.split(" ", 1)[1]
                    if len(tail) >= 5 and self._similarity(tail, target) >= 0.80:
                        return True

        return False

    # =========================================================
    # VAD
    # =========================================================
    def _detect_speech_regions(self, audio_float32):
        if len(audio_float32) == 0:
            return []

        audio_tensor = torch.from_numpy(audio_float32)
        speech_timestamps = get_speech_timestamps(
            audio_tensor,
            self.vad_model,
            sampling_rate=self.input_samplerate,
            return_seconds=False,
        )
        return speech_timestamps

    def _has_speech(self, audio_float32, min_speech_ms=120):
        regions = self._detect_speech_regions(audio_float32)
        min_samples = int(self.input_samplerate * min_speech_ms / 1000)

        for region in regions:
            if (region["end"] - region["start"]) >= min_samples:
                return True
        return False

    # =========================================================
    # STT
    # =========================================================
    def _transcribe(self, audio_float32, beam_size=1):
        if len(audio_float32) == 0:
            return ""

        prepared = self._normalize_audio(audio_float32)

        segments, _ = self.whisper.transcribe(
            prepared,
            language=self.lang,
            beam_size=beam_size,
            vad_filter=False,
        )

        text_parts = []
        for segment in segments:
            if segment.text:
                text_parts.append(segment.text.strip())

        return " ".join(t for t in text_parts if t).strip()

    def listen_command_vad(
        self,
        start_timeout_sec=3.5,
        max_record_sec=8.0,
        silence_to_stop_ms=1100,
        min_speech_ms=120,
        prebuffer_ms=800,
    ):
        print("\n[Dinleniyor...] Komutunu bekliyorum...")

        audio = self._record_blocks_until(
            start_timeout_sec=start_timeout_sec,
            max_record_sec=max_record_sec,
            silence_to_stop_ms=silence_to_stop_ms,
            min_speech_ms=min_speech_ms,
            prebuffer_ms=prebuffer_ms,
        )

        if audio is None or len(audio) == 0:
            return None

        audio = self._normalize_audio(audio)

        if not self._has_speech(audio, min_speech_ms=min_speech_ms):
            return None

        text = self._transcribe(audio, beam_size=1)
        if text:
            print(f"Tanem: {text}")
            return text.lower()

        return None

    # =========================================================
    # ARKA PLAN WAKE LISTENER
    # =========================================================
    def _wake_loop(self, listen_window_sec=1.6, post_wake_command_sec=8.0):
        print("\n[UYKU MODU] Wake word sürekli arka planda dinleniyor...")

        while self._wake_running:
            try:
                if self._busy or (time.time() - self._last_tts_time < self._tts_cooldown_sec):
                    time.sleep(0.15)
                    continue

                audio = self._record_fixed(listen_window_sec)
                if len(audio) == 0:
                    continue

                audio = self._normalize_audio(audio)

                if not self._has_speech(audio, min_speech_ms=100):
                    continue

                text = self._transcribe(audio, beam_size=1)
                if not text:
                    continue

                print(f">>> [WAKE CHECK] {text}")

                if self._contains_wake_word(text):
                    print(">>> [WAKE WORD] Algılandı.")
                    self._busy = True

                    command = self.listen_command_vad(
                        start_timeout_sec=3.5,
                        max_record_sec=post_wake_command_sec,
                        silence_to_stop_ms=1100,
                        min_speech_ms=120,
                        prebuffer_ms=800,
                    )

                    if command:
                        self.command_queue.put({"type": "command", "text": command})
                    else:
                        self.command_queue.put({"type": "empty", "text": None})

                    self._busy = False

            except Exception as e:
                self._busy = False
                print(f">>> [WAKE LOOP HATASI] {type(e).__name__}: {e}")
                time.sleep(0.4)

    def start_wake_listener(self):
        if self._wake_thread and self._wake_thread.is_alive():
            return
        self._wake_running = True
        self._wake_thread = threading.Thread(target=self._wake_loop, daemon=True)
        self._wake_thread.start()

    def stop_wake_listener(self):
        self._wake_running = False

    def get_pending_command(self):
        try:
            return self.command_queue.get_nowait()
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

        except Exception as e:
            print(f">>> [TTS HATASI] {type(e).__name__}: {e}")

        finally:
            self._busy = False
            if temp_path and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except Exception:
                    pass
