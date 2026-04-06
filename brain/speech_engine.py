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
    def __init__(self, lang="tr", input_device_index=-1):
        self.lang = lang
        self.sample_rate = 16000
        self.frame_length = 512

        self.event_queue = queue.Queue()
        self.stt_queue = queue.Queue()

        self._listener_running = False
        self._busy = False
        self._muted = False
        self._last_tts_time = 0.0
        self._tts_cooldown_sec = 2.2
        self._shutting_down = False

        self.recorder = None
        self.audio_lock = threading.Lock()
        self.listener_thread = None
        self.stt_worker_thread = None

        log_time(">>> Modeller yükleniyor (Whisper/VAD/Piper)...")
        self.stt_model = WhisperModel("small", device="cpu", compute_type="int8")
        self.vad_model = load_silero_vad()
        self.voice = PiperVoice.load("tr_TR-fahrettin-medium.onnx")

        self.device_index = input_device_index
        log_time(">>> [SES] Tüm sistemler hazır.")

    def debug_list_input_devices(self):
        devices = PvRecorder.get_available_devices()
        log_time(">>> [MIC DEBUG] Cihaz Listesi:")
        for i, name in enumerate(devices):
            print(f"    #{i}: {name}")

    def is_muted(self):
        return self._muted

    def set_busy(self, val):
        self._busy = val

    def start_auto_listener(self):
        if self._listener_running:
            return

        self._listener_running = True
        self._shutting_down = False

        self.stt_worker_thread = threading.Thread(target=self._stt_worker_loop, daemon=False)
        self.stt_worker_thread.start()

        self.listener_thread = threading.Thread(target=self._listener_loop, daemon=False)
        self.listener_thread.start()

        log_time("[DINLEME MODU] Arka plan dinlemesi aktif.")

    def stop_auto_listener(self):
        self._listener_running = False
        self._shutting_down = True

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
            self.listener_thread.join(timeout=2.0)

        if self.stt_worker_thread and self.stt_worker_thread.is_alive():
            self.stt_worker_thread.join(timeout=4.0)

        if self.recorder:
            try:
                self.recorder.delete()
            except Exception:
                pass
            self.recorder = None

    def get_pending_event(self):
        try:
            return self.event_queue.get_nowait()
        except queue.Empty:
            return {"type": "none"}

    def _has_speech(self, audio_float32, threshold=0.35):
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

    def _listener_loop(self):
        pre_roll_frames = 12
        silence_limit_frames = 28
        analysis_window_frames = 10

        try:
            self.recorder = PvRecorder(
                device_index=self.device_index,
                frame_length=self.frame_length
            )
            self.recorder.start()

            ring_buffer = deque(maxlen=pre_roll_frames)
            analysis_buffer = deque(maxlen=analysis_window_frames)

            collected_audio = []
            silent_frames = 0
            recording = False

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
                    silent_frames = 0
                    continue

                if time.time() - self._last_tts_time < self._tts_cooldown_sec:
                    continue

                frame_np = np.array(frame, dtype=np.int16)
                frame_f32 = frame_np.astype(np.float32) / 32768.0

                ring_buffer.append(frame_np)
                analysis_buffer.append(frame_f32)

                if len(analysis_buffer) < analysis_window_frames:
                    continue

                window = np.concatenate(list(analysis_buffer)).astype(np.float32)
                speech_detected = self._has_speech(window, threshold=0.30)

                if speech_detected:
                    if not recording:
                        log_time(">>> [AUDIO] Ses algılandı (VAD tetiklendi)...")
                        recording = True
                        collected_audio = []

                        for old_frame in ring_buffer:
                            collected_audio.extend(old_frame.tolist())

                    collected_audio.extend(frame_np.tolist())
                    silent_frames = 0

                elif recording:
                    collected_audio.extend(frame_np.tolist())
                    silent_frames += 1

                    if silent_frames >= silence_limit_frames:
                        log_time(">>> [VAD] Konuşma bitti, STT kuyruğa alınıyor...")
                        audio_data = np.array(collected_audio, dtype=np.int16)

                        if len(audio_data) >= int(self.sample_rate * 0.5):
                            try:
                                self.stt_queue.put_nowait(audio_data)
                            except Exception:
                                pass

                        collected_audio = []
                        recording = False
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

    def _stt_worker_loop(self):
        while not self._shutting_down:
            try:
                item = self.stt_queue.get(timeout=0.5)
            except queue.Empty:
                continue

            if item is None:
                break

            try:
                self._process_speech(item)
            except Exception as e:
                if not self._shutting_down:
                    log_time(f">>> [STT WORKER ERROR] {type(e).__name__}: {e}")

    def _normalize_text(self, text: str) -> str:
        t = text.lower().strip()
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

    def _text_quality(self, text: str) -> str:
        """
        Dönen değerler:
        - good
        - weak
        - bad
        """
        n = self._normalize_text(text)
        if not n:
            return "bad"

        tokens = n.split()
        if len(tokens) == 0:
            return "bad"

        weak_words = {
            "sultan", "aba", "baba", "tamam", "peki", "hmm", "evet", "hey"
        }

        if len(tokens) == 1:
            if tokens[0] in weak_words:
                return "bad"
            if len(tokens[0]) <= 3:
                return "bad"

        if len(tokens) == 2:
            if all(len(t) <= 5 for t in tokens):
                return "weak"

        question_words = {"ne", "neden", "nasil", "hangi", "kim", "mi", "mı", "mu", "mü"}
        has_question_signal = any(q in n for q in question_words)

        if not has_question_signal and len(tokens) <= 2:
            return "weak"

        return "good"

    def _process_speech(self, audio_int16):
        if len(audio_int16) == 0:
            return

        if len(audio_int16) < self.sample_rate * 0.5:
            return

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            with wave.open(tmp_path, "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(self.sample_rate)
                wf.writeframes(audio_int16.tobytes())

            segments, _ = self.stt_model.transcribe(
                tmp_path,
                language=self.lang,
                beam_size=2,
                vad_filter=False,
                condition_on_previous_text=False,
                initial_prompt=(
                    "Türkçe konuşma. Günlük konuşma. Robot asistan. "
                    "Kullanıcı doğal cümleler kuruyor. Bozuk STT durumunda uydurma yapma."
                ),
            )
            text = " ".join([s.text.strip() for s in segments if s.text]).strip()

        finally:
            try:
                os.remove(tmp_path)
            except Exception:
                pass

        if not text or len(text) < 2:
            return

        log_time(f">>> [STT] '{text}'")

        lower = text.lower()

        if any(w in lower for w in ["sus", "sessiz ol", "dur"]):
            self._muted = True
            log_time(">>> [MODE] Sessiz mod.")
            self.event_queue.put({"type": "sleep"})
            return

        if self._muted and ("hey" in lower):
            self._muted = False
            log_time(">>> [MODE] Aktif mod.")
            self.event_queue.put({"type": "resumed"})
            return

        quality = self._text_quality(text)
        log_time(f">>> [STT QUALITY] {quality}")

        if quality == "bad":
            self.event_queue.put({
                "type": "clarify",
                "text": "Seni tam anlayamadım. Son cümleni biraz daha net tekrar eder misin?"
            })
            return

        if quality == "weak":
            self.event_queue.put({
                "type": "clarify",
                "text": "Son söylediğini tam çıkaramadım. Bir kez daha söyler misin?"
            })
            return

        if not self._muted:
            self.event_queue.put({"type": "command", "text": text})

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

    def speak(self, text):
        if not text:
            return

        log_time(f"Poodle: {text}")
        self._busy = True

        temp_path = None
        try:
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

            cmd = "/usr/bin/afplay" if platform.system() == "Darwin" else "aplay"
            subprocess.run([cmd, temp_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            self._last_tts_time = time.time()

        finally:
            if temp_path:
                try:
                    os.remove(temp_path)
                except Exception:
                    pass
            self._busy = False
