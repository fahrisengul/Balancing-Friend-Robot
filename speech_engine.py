import os
import wave
import tempfile
import threading
import platform
import subprocess
import time
import queue
from datetime import datetime
from collections import deque
import array
import re
from typing import List, Optional

from pvrecorder import PvRecorder
import numpy as np
import torch
from faster_whisper import WhisperModel
from piper.voice import PiperVoice
from silero_vad import load_silero_vad, get_speech_timestamps


def get_now():
    return datetime.now().strftime("%H:%M:%S.%f")[:-3]


def log_time(message):
    print(f"[{get_now()}] {message}")


class PoodleSpeech:
    def __init__(
        self,
        lang: str = "tr",
        input_device_index: Optional[int] = None,
        preferred_input_names: Optional[List[str]] = None,
    ):
        self.lang = lang
        self.sample_rate = 16000
        self.frame_length = 512

        self.event_queue = queue.Queue()
        self.stt_queue = queue.Queue(maxsize=2)

        self._listener_running = False
        self._busy = False
        self._muted = False
        self._shutting_down = False

        self._last_tts_time = 0.0
        self._tts_cooldown_sec = 3.5
        self._last_spoken_text = ""
        self._last_spoken_text_norm = ""

        self._input_level = 0.0
        self._tts_level = 0.0
        self._tts_peak_level = 0.0
        self._tts_play_until = 0.0

        self.recorder = None
        self.audio_lock = threading.Lock()
        self.listener_thread = None
        self.stt_worker_thread = None

        self.preferred_input_names = preferred_input_names or [
            "MacBook Pro Mikrofonu",
            "FahriSengul Mikrofonu",
            "Jabra",
        ]
        self.device_index = input_device_index
        self.device_name = None

        log_time(">>> Modeller yükleniyor (Whisper/VAD/Piper)...")
        self.stt_model = WhisperModel("small", device="cpu", compute_type="int8")
        self.vad_model = load_silero_vad()
        self.voice = PiperVoice.load("tr_TR-fahrettin-medium.onnx")
        log_time(">>> [SES] Tüm sistemler hazır.")

    # ---------------------------------------------------------
    # DEVICE SELECTION
    # ---------------------------------------------------------
    def debug_list_input_devices(self):
        devices = PvRecorder.get_available_devices()
        log_time(">>> [MIC DEBUG] Cihaz Listesi:")
        for i, name in enumerate(devices):
            print(f"    #{i}: {name}")

    def _auto_select_input_device(self):
        devices = PvRecorder.get_available_devices()
      
        if self.device_index is not None:
            if 0 <= self.device_index < len(devices):
                self.device_name = devices[self.device_index]
                log_time(f">>> [MIC ACTIVE] Manuel seçim: #{self.device_index} {self.device_name}")
                return
            log_time(">>> [MIC ACTIVE] Verilen input_device_index geçersiz. Otomatik seçime geçiliyor.")
            self.device_index = None

        lowered_devices = [(i, name, name.lower()) for i, name in enumerate(devices)]

        for preferred in self.preferred_input_names:
            p = preferred.lower()
            for i, name, lowered in lowered_devices:
                if p in lowered:
                    self.device_index = 0
                    self.device_name = name
                    log_time(f">>> [MIC ACTIVE] Otomatik seçim: #{i} {name}")
                    return

        if devices:
            self.device_index = 0
            self.device_name = devices[0]
            log_time(f">>> [MIC ACTIVE] Fallback seçim: #{self.device_index} {self.device_name}")
        else:
            self.device_index = -1
            self.device_name = "default"
            log_time(">>> [MIC ACTIVE] Cihaz listesi boş, default kullanılacak.")

    # ---------------------------------------------------------
    # PUBLIC
    # ---------------------------------------------------------
    def is_muted(self):
        return self._muted

    def set_busy(self, val):
        self._busy = val

    def get_visual_state(self):
        now = time.time()

        if now >= self._tts_play_until:
            self._tts_level *= 0.90

        self._input_level *= 0.92

        return {
            "input_level": float(max(0.0, min(1.0, self._input_level))),
            "tts_level": float(max(0.0, min(1.0, self._tts_level))),
        }

    def start_auto_listener(self):
        if self._listener_running:
            return

        self._auto_select_input_device()

        self._listener_running = True
        self._shutting_down = False

        self.stt_worker_thread = threading.Thread(
            target=self._stt_worker_loop,
            daemon=True
        )
        self.stt_worker_thread.start()

        self.listener_thread = threading.Thread(
            target=self._listener_loop,
            daemon=True
        )
        self.listener_thread.start()

        log_time("[DINLEME MODU] Arka plan dinlemesi aktif.")

    def stop_auto_listener(self):
        self._listener_running = False
        self._shutting_down = True

        self._flush_stt_queue()

        try:
            self.stt_queue.put_nowait(None)
        except Exception:
            pass

        if self.recorder:
            try:
                self.recorder.stop()
            except Exception:
                pass

        if self.listener_thread and self.listener_thread.is_alive():
            self.listener_thread.join(timeout=1.0)

        if self.stt_worker_thread and self.stt_worker_thread.is_alive():
            self.stt_worker_thread.join(timeout=2.0)

        if self.recorder:
            try:
                self.recorder.delete()
            except Exception:
                pass
            self.recorder = None

    def stop(self):
        self.stop_auto_listener()

    def get_pending_event(self):
        try:
            return self.event_queue.get_nowait()
        except queue.Empty:
            return {"type": "none"}

    # ---------------------------------------------------------
    # INTERNAL HELPERS
    # ---------------------------------------------------------
    def _flush_stt_queue(self):
        flushed = 0
        while True:
            try:
                item = self.stt_queue.get_nowait()
                if item is None:
                    continue
                flushed += 1
            except queue.Empty:
                break
        if flushed:
            log_time(f">>> [STT QUEUE] Temizlendi. dropped={flushed}")

    def _queue_audio_segment(self, audio_data: np.ndarray):
        if self._busy or self._shutting_down:
            return

        try:
            self.stt_queue.put_nowait((time.time(), audio_data))
            log_time(f">>> [STT QUEUE] Segment eklendi. samples={len(audio_data)}")
        except queue.Full:
            try:
                _ = self.stt_queue.get_nowait()
                log_time(">>> [STT QUEUE] Eski segment düşürüldü.")
            except queue.Empty:
                pass

            try:
                self.stt_queue.put_nowait((time.time(), audio_data))
                log_time(f">>> [STT QUEUE] Yeni segment zorla eklendi. samples={len(audio_data)}")
            except Exception:
                log_time(">>> [STT QUEUE] Segment tamamen atlandı.")

    def _has_speech(self, audio_float32, threshold=0.42):
        if len(audio_float32) == 0:
            return False

        audio_tensor = torch.from_numpy(audio_float32)
        speech_ts = get_speech_timestamps(
            audio_tensor,
            self.vad_model,
            sampling_rate=self.sample_rate,
            threshold=threshold,
        )
        return len(speech_ts) > 0

    def _rms(self, audio_float32) -> float:
        if len(audio_float32) == 0:
            return 0.0
        return float(np.sqrt(np.mean(np.square(audio_float32))))

    def _is_silent(self, audio_float32, threshold=0.02) -> bool:
        return self._rms(audio_float32) < threshold

    def _normalize_text(self, text: str) -> str:
        t = (text or "").lower().strip()
        t = (
            t.replace("ı", "i")
             .replace("ğ", "g")
             .replace("ş", "s")
             .replace("ç", "c")
             .replace("ö", "o")
             .replace("ü", "u")
        )
        t = re.sub(r"[^a-z0-9\s]", " ", t)
        t = re.sub(r"\s+", " ", t).strip()
        return t

    def _looks_like_prompt_leakage(self, normalized: str) -> bool:
        leakage_markers = [
            "kisa dogal diyalog",
            "kisa ve dogal cumleler",
            "robotun adi poodle",
            "robotun adı poodle",
            "turkce gunluk konusma",
            "bozuk tahmin uretme",
            "izlediginiz icin tesekkurler",
            "abone olmayi unutmayin",
        ]
        return any(m in normalized for m in leakage_markers)

    def _looks_like_echo_of_last_tts(self, normalized_text: str) -> bool:
        if not normalized_text or not self._last_spoken_text_norm:
            return False

        now = time.time()
        if now - self._last_tts_time > self._tts_cooldown_sec:
            return False

        a = set(normalized_text.split())
        b = set(self._last_spoken_text_norm.split())

        if not a or not b:
            return False

        overlap = len(a & b) / max(1, len(a))
        return overlap >= 0.6

    def _auto_gain_for_stt(self, audio_int16: np.ndarray) -> np.ndarray:
        audio = audio_int16.astype(np.float32) / 32768.0
        rms = self._rms(audio)

        if rms <= 1e-6:
            return audio_int16

        target_rms = 0.08
        gain = target_rms / rms
        gain = max(0.6, min(gain, 3.0))

        boosted = audio * gain
        boosted = np.clip(boosted, -1.0, 1.0)

        return (boosted * 32767.0).astype(np.int16)

    def _is_whitelisted_short_utterance(self, normalized: str) -> bool:
        whitelist_phrases = {
            "selam",
            "merhaba",
            "nasilsin",
            "adin ne",
            "sen kimsin",
            "tesekkur ederim",
            "tesekkurler",
            "beni duyabiliyor musun",
            "beni duyuyor musun",
            "gorusuruz",
            "hosca kal",
            "saat kac",
            "bugun gunlerden ne",
        }
        return normalized in whitelist_phrases

    def _is_wake_phrase(self, normalized: str) -> bool:
        wake_phrases = {
            "hey",
            "hey poodle",
            "hey puddle",
            "hey pudil",
            "poodle",
        }
        return normalized in wake_phrases

    def _text_quality(self, text: str) -> str:
        n = self._normalize_text(text)
        if not n:
            return "bad"

        tokens = n.split()
        if len(tokens) == 0:
            return "bad"

        if self._looks_like_prompt_leakage(n):
            return "bad"

        if self._looks_like_echo_of_last_tts(n):
            return "bad"

        if self._is_whitelisted_short_utterance(n):
            return "good"

        if self._is_wake_phrase(n):
            return "good"

        if len(tokens) == 1:
            tok = tokens[0]
            if tok in {"selam", "merhaba", "nasilsin", "gorusuruz", "poodle"}:
                return "good"
            if len(tok) <= 2:
                return "bad"
            return "weak"

        if 2 <= len(tokens) <= 5:
            return "good"

        return "good"

    # ---------------------------------------------------------
    # LISTENER
    # ---------------------------------------------------------
    def _listener_loop(self):
        pre_roll_frames = 12
        silence_limit_frames = 28
        analysis_window_frames = 10

        try:
            recorder_index = self.device_index if self.device_index is not None else -1
            self.recorder = PvRecorder(
                device_index=recorder_index,
                frame_length=self.frame_length
            )
            self.recorder.start()

            ring_buffer = deque(maxlen=pre_roll_frames)
            analysis_buffer = deque(maxlen=analysis_window_frames)

            collected_audio = []
            silent_frames = 0
            recording = False
            recording_start_ts = None

            while self._listener_running and not self._shutting_down:
                try:
                    frame = self.recorder.read()
                except Exception as e:
                    if self._shutting_down:
                        break
                    log_time(f">>> [RECORDER READ ERROR] {type(e).__name__}: {e}")
                    break

                if self._busy:
                    ring_buffer.clear()
                    analysis_buffer.clear()
                    collected_audio = []
                    recording = False
                    recording_start_ts = None
                    silent_frames = 0
                    continue

                if time.time() - self._last_tts_time < self._tts_cooldown_sec:
                    continue

                frame_np = np.array(frame, dtype=np.int16)
                frame_f32 = frame_np.astype(np.float32) / 32768.0

                rms = self._rms(frame_f32)
                norm_rms = min(1.0, rms * 18.0)
                self._input_level += (norm_rms - self._input_level) * 0.35

                # gain control öncesi dinleme tarafı için sert gate
                if self._is_silent(frame_f32, threshold=0.02) and not recording:
                    continue

                ring_buffer.append(frame_np)
                analysis_buffer.append(frame_f32)

                if len(analysis_buffer) < analysis_window_frames:
                    continue

                window = np.concatenate(list(analysis_buffer)).astype(np.float32)
                speech_detected = self._has_speech(window, threshold=0.42)

                if speech_detected:
                    if not recording:
                        log_time(">>> [AUDIO] Ses algılandı (VAD tetiklendi)...")
                        recording = True
                        recording_start_ts = time.time()
                        collected_audio = []

                        for old_frame in ring_buffer:
                            collected_audio.extend(old_frame.tolist())

                    collected_audio.extend(frame_np.tolist())
                    silent_frames = 0

                elif recording:
                    collected_audio.extend(frame_np.tolist())
                    silent_frames += 1

                    if silent_frames >= silence_limit_frames:
                        audio_data = np.array(collected_audio, dtype=np.int16)
                        seconds = len(audio_data) / self.sample_rate
                        log_time(f">>> [VAD] Konuşma bitti, STT kuyruğa alınıyor... ({seconds:.2f}s)")

                        # minimum speech duration filter
                        if seconds >= 0.9:
                            self._queue_audio_segment(audio_data)
                        else:
                            log_time(">>> [VAD FILTER] Çok kısa segment, atlandı.")

                        collected_audio = []
                        recording = False
                        recording_start_ts = None
                        silent_frames = 0
                        ring_buffer.clear()
                        analysis_buffer.clear()

        except Exception as e:
            if not self._shutting_down:
                log_time(f">>> [RECORDER ERROR] {type(e).__name__}: {e}")

        finally:
            try:
                if self.recorder:
                    self.recorder.stop()
            except Exception:
                pass

    # ---------------------------------------------------------
    # STT WORKER
    # ---------------------------------------------------------
    def _stt_worker_loop(self):
        log_time(">>> [STT WORKER] Hazır.")
        while not self._shutting_down:
            try:
                item = self.stt_queue.get(timeout=0.5)
            except queue.Empty:
                continue

            if item is None:
                log_time(">>> [STT WORKER] Kapatma sinyali alındı.")
                break

            queued_at, audio = item

            if time.time() - queued_at > 2.5:
                log_time(">>> [STT WORKER] Bayat segment atlandı.")
                continue

            try:
                if self._shutting_down:
                    break
                log_time(f">>> [STT WORKER] Segment işleniyor... samples={len(audio)}")
                self._process_speech(audio)
                log_time(">>> [STT WORKER] Segment tamamlandı.")
            except Exception as e:
                if not self._shutting_down:
                    log_time(f">>> [STT WORKER ERROR] {type(e).__name__}: {e}")

        log_time(">>> [STT WORKER] Durdu.")

    # ---------------------------------------------------------
    # STT TRANSCRIBE
    # ---------------------------------------------------------
    def _transcribe_audio(self, tmp_path: str) -> str:
        segments, _ = self.stt_model.transcribe(
            tmp_path,
            language=self.lang,
            beam_size=2,
            vad_filter=False,
            condition_on_previous_text=False,
            initial_prompt=(
                "Turkce gunluk konusma. "
                "Kisa ve dogal cumleler. "
                "Ornek: merhaba, nasilsin, bugun ne yaptin. "
                "Bozuk tahmin uretme."
            ),
        )
        text = " ".join([s.text.strip() for s in segments if s.text]).strip()
        return text

    def _process_speech(self, audio_int16):
        if len(audio_int16) == 0:
            log_time(">>> [STT] Boş segment, atlandı.")
            return

        if len(audio_int16) < self.sample_rate * 0.5:
            log_time(">>> [STT] Çok kısa segment, atlandı.")
            return

        # gain control
        audio_int16 = self._auto_gain_for_stt(audio_int16)

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            with wave.open(tmp_path, "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(self.sample_rate)
                wf.writeframes(audio_int16.tobytes())

            text = self._transcribe_audio(tmp_path)

        except Exception as e:
            log_time(f">>> [STT TRANSCRIBE ERROR] {type(e).__name__}: {e}")
            return

        finally:
            try:
                os.remove(tmp_path)
            except Exception:
                pass

        if not text or len(text.strip()) < 3:
            log_time(">>> [STT] Boş transkript döndü.")
            return

        log_time(f">>> [STT] '{text}'")

        normalized = self._normalize_text(text)

        if self._looks_like_prompt_leakage(normalized):
            log_time(">>> [STT] Prompt leakage algılandı, segment atlandı.")
            return

        if self._looks_like_echo_of_last_tts(normalized):
            log_time(">>> [STT] TTS echo algılandı, segment atlandı.")
            return

        if normalized in {"sus", "sessiz ol", "dur"}:
            self._muted = True
            log_time(">>> [MODE] Sessiz mod.")
            self.event_queue.put({"type": "sleep"})
            return

        if self._is_wake_phrase(normalized):
            if self._muted:
                self._muted = False
                log_time(">>> [MODE] Aktif mod.")
                self.event_queue.put({"type": "resumed"})
            else:
                self.event_queue.put({"type": "command", "text": "Hey Poodle"})
            return

        quality = self._text_quality(text)
        log_time(f">>> [STT QUALITY] {quality}")

        if quality == "bad":
            self.event_queue.put({
                "type": "clarify",
                "text": "Seni tam anlayamadım. Bir daha söyler misin?"
            })
            return

        if quality == "weak":
            self.event_queue.put({
                "type": "clarify",
                "text": "Galiba tam duyamadım. Daha net söyler misin?"
            })
            return

        if not self._muted and not self._busy:
            self.event_queue.put({"type": "command", "text": text})

    # ---------------------------------------------------------
    # TTS
    # ---------------------------------------------------------
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

        raise RuntimeError(f"AudioChunk çözümlenemedi: {type(chunk)}")

    def _tts(self, text):
        temp_path = None
        sample_rate = self.voice.config.sample_rate
        pcm_buffer = bytearray()

        for chunk in self.voice.synthesize(text):
            chunk_bytes = self._chunk_to_bytes(chunk)
            if chunk_bytes:
                pcm16 = np.frombuffer(chunk_bytes, dtype=np.int16).astype(np.float32) / 32768.0
                if len(pcm16):
                    rms = self._rms(pcm16)
                    level = min(1.0, rms * 14.0)
                    if level > self._tts_peak_level:
                        self._tts_peak_level = level
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

        duration_sec = len(pcm_buffer) / (2 * sample_rate)
        self._tts_level = max(0.15, min(1.0, self._tts_peak_level if self._tts_peak_level > 0 else 0.35))
        self._tts_play_until = time.time() + duration_sec
        self._tts_peak_level = 0.0

        cmd = "/usr/bin/afplay" if platform.system() == "Darwin" else "aplay"
        subprocess.run([cmd, temp_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        if temp_path:
            try:
                os.remove(temp_path)
            except Exception:
                pass

    def speak(self, text):
        if not text:
            return

        log_time(f"Poodle: {text}")
        self._busy = True
        self._flush_stt_queue()

        self._last_spoken_text = text
        self._last_spoken_text_norm = self._normalize_text(text)

        try:
            self._tts(text)
            self._last_tts_time = time.time()
        finally:
            time.sleep(0.2)
            self._busy = False
