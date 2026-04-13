import os
import wave
import tempfile
import threading
import platform
import subprocess
import time
from datetime import datetime
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
        self.frame_length = 512
        self.event_queue = []

        self._listener_running = False
        self._shutting_down = False
        self._busy = False
        self._muted = False

        self.recorder = None
        self.listener_thread = None
        self._recorder_lock = threading.Lock()

        self._pending_phrase = ""
        self._pending_phrase_since = 0.0
        self._min_phrase_chars = 28
        self._max_phrase_wait_sec = 0.7
        self._last_tts_time = 0.0
        self._tts_cooldown_sec = 0.65

        log_time(">>> Modeller yükleniyor (Whisper/VAD/Piper)...")
        self.stt_model = WhisperModel("base", device="cpu", compute_type="int8")
        self.vad_model = load_silero_vad()
        self.voice = PiperVoice.load("tr_TR-fahrettin-medium.onnx")

        self.device_index = input_device_index
        log_time(">>> [SES] Tüm sistemler hazır.")

    # =========================================================
    # DEBUG / DEVICE
    # =========================================================
    def debug_list_input_devices(self):
        devices = PvRecorder.get_available_devices()
        log_time(">>> [MIC DEBUG] Cihaz Listesi:")
        for i, name in enumerate(devices):
            print(f"    #{i}: {name}")

    def select_default_input_device(self):
        devices = PvRecorder.get_available_devices()

        if self.device_index is not None and self.device_index >= 0:
            if self.device_index < len(devices):
                log_time(f">>> [MIC ACTIVE] Manuel seçim: #{self.device_index} {devices[self.device_index]}")
                return self.device_index

        self.device_index = -1

        try:
            default_name = devices[0] if devices else "Default"
            log_time(f">>> [MIC ACTIVE] Otomatik seçim: #0 {default_name}")
        except Exception:
            log_time(">>> [MIC ACTIVE] Otomatik seçim: default cihaz")

        return self.device_index

    # =========================================================
    # STATE
    # =========================================================
    def is_muted(self):
        return self._muted

    def set_busy(self, val):
        self._busy = val

    # =========================================================
    # AUTO LISTENER
    # =========================================================
    def start_auto_listener(self):
        if self._listener_running:
            return

        self._listener_running = True
        self._shutting_down = False
        self.listener_thread = threading.Thread(target=self._listener_loop, daemon=True)
        self.listener_thread.start()
        log_time("[DINLEME MODU] Arka plan dinlemesi aktif.")

    def stop_auto_listener(self):
        self._listener_running = False
        self._shutting_down = True

        # Thread'in recorder.read() içinden kontrollü çıkabilmesi için
        # recorder cleanup yalnız burada yapılır.
        if self.listener_thread and self.listener_thread.is_alive():
            self.listener_thread.join(timeout=2.5)

        with self._recorder_lock:
            if self.recorder is not None:
                try:
                    self.recorder.stop()
                except Exception:
                    pass

                try:
                    self.recorder.delete()
                except Exception:
                    pass

                self.recorder = None

        self.listener_thread = None

    def get_pending_event(self):
        if len(self.event_queue) > 0:
            return self.event_queue.pop(0)
        return {"type": "none"}

    def get_pending_command(self):
        evt = self.get_pending_event()
        if evt.get("type") == "command":
            return evt.get("text")
        return None

    # =========================================================
    # LISTENER LOOP
    # =========================================================
    def _listener_loop(self):
        local_recorder = None

        try:
            local_recorder = PvRecorder(
                device_index=self.device_index,
                frame_length=self.frame_length
            )
            local_recorder.start()

            with self._recorder_lock:
                self.recorder = local_recorder

            collected_audio = []
            silent_frames = 0
            recording = False

            while self._listener_running and not self._shutting_down:
                try:
                    frame = local_recorder.read()
                except Exception as e:
                    if self._shutting_down:
                        break
                    log_time(f">>> [RECORDER READ ERROR] {type(e).__name__}: {e}")
                    break

                if self._shutting_down:
                    break

                if self._busy:
                    collected_audio = []
                    recording = False
                    silent_frames = 0
                    continue

                audio_float32 = np.array(frame, dtype=np.float32) / 32768.0
                audio_tensor = torch.from_numpy(audio_float32)

                speech_ts = get_speech_timestamps(
                    audio_tensor,
                    self.vad_model,
                    sampling_rate=16000,
                    threshold=0.3,
                )

                if len(speech_ts) > 0:
                    if not recording:
                        log_time(">>> [AUDIO] Ses algılandı (VAD tetiklendi)...")
                        recording = True

                    collected_audio.extend(frame)
                    silent_frames = 0

                elif recording:
                    collected_audio.extend(frame)
                    silent_frames += 1

                    if silent_frames > 40:
                        log_time(">>> [VAD] Konuşma bitti, STT başlıyor...")
                        audio_data = np.array(collected_audio, dtype=np.int16)
                        threading.Thread(
                            target=self._process_speech,
                            args=(audio_data,),
                            daemon=True
                        ).start()

                        collected_audio = []
                        recording = False
                        silent_frames = 0

        except Exception as e:
            log_time(f">>> [RECORDER ERROR] {type(e).__name__}: {e}")

        finally:
            # Recorder cleanup burada yapılmıyor.
            # Double delete / race condition'i önlemek için tek cleanup noktası stop_auto_listener().
            pass

    # =========================================================
    # STT
    # =========================================================
    def _process_speech(self, audio_int16):
        if self._shutting_down:
            return

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            with wave.open(tmp_path, "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(16000)
                wf.writeframes(audio_int16.tobytes())

            segments, _ = self.stt_model.transcribe(tmp_path, language=self.lang)
            text = " ".join([s.text for s in segments]).strip()

        finally:
            try:
                os.remove(tmp_path)
            except Exception:
                pass

        if self._shutting_down:
            return

        if not text or len(text) < 2:
            return

        log_time(f">>> [STT] '{text}'")

        lowered = text.lower()

        if any(w in lowered for w in ["sus", "sessiz ol", "dur"]):
            self._muted = True
            log_time(">>> [MODE] Sessiz mod.")
            self.event_queue.append({"type": "sleep"})
            return

        if self._muted and any(w in lowered for w in ["uyan", "devam et", "konuşabilirsin", "hey"]):
            self._muted = False
            log_time(">>> [MODE] Aktif mod.")
            self.event_queue.append({"type": "resumed"})
            return

        if not self._muted:
            self.event_queue.append({"type": "command", "text": text})

    # =========================================================
    # TTS
    # =========================================================
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
                self._speak_now(self._pending_phrase)
                self._pending_phrase = ""
                self._pending_phrase_since = 0.0
            return

        if self._pending_phrase:
            combined = f"{self._pending_phrase} {cleaned}".strip()
            cleaned = self._clean_tts_text(combined)
            self._pending_phrase = ""
            self._pending_phrase_since = 0.0

        self._speak_now(cleaned)

    def flush_pending_tts(self):
        if self._pending_phrase:
            text = self._clean_tts_text(self._pending_phrase)
            self._pending_phrase = ""
            self._pending_phrase_since = 0.0
            if text:
                self._speak_now(text)

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

    def _speak_now(self, text):
        if not text or self._shutting_down:
            return

        log_time(f"Poodle: {text}")
        self._busy = True

        temp_path = None
        try:
            now = time.time()
            delta = now - self._last_tts_time
            if delta < self._tts_cooldown_sec:
                time.sleep(self._tts_cooldown_sec - delta)

            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                temp_path = tmp.name

            with wave.open(temp_path, "wb") as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(self.voice.config.sample_rate)
                self.voice.synthesize(text, wav_file)

            cmd = "afplay" if platform.system() == "Darwin" else "aplay"
            subprocess.run([cmd, temp_path], check=False)

            self._last_tts_time = time.time()

        finally:
            try:
                if temp_path and os.path.exists(temp_path):
                    os.remove(temp_path)
            except Exception:
                pass
            self._busy = False
