import threading
import time
from datetime import datetime

import numpy as np
from pvrecorder import PvRecorder

from .audio_devices import debug_list_input_devices as _debug_list_input_devices
from .audio_devices import select_default_input_device as _select_default_input_device
from .stt_service import STTService
from .tts_buffer import TTSBuffer
from .tts_service import TTSService


def now():
    return datetime.now().strftime("%H:%M:%S.%f")[:-3]


def log_time(msg):
    print(f"[{now()}] {msg}")


class PoodleSpeech:
    def __init__(self, lang="tr", input_device_index=-1):
        self.lang = lang
        self.frame_length = 512
        self.event_queue = []

        self._listener_running = False
        self._busy = False
        self._paused = False
        self._muted = False

        self.device_index = input_device_index
        self.recorder = None

        log_time(">>> Modeller yükleniyor (Whisper/VAD/Piper)...")

        # STT INIT (owner required)
        self.stt_service = STTService(self)

        self._tts_service = TTSService(self)
        self._tts_buffer = TTSBuffer(self)

        log_time(">>> [SES] Tüm sistemler hazır.")

    # ---------------------------------------------------------
    # AUDIO DEVICE
    # ---------------------------------------------------------
    def debug_list_input_devices(self):
        _debug_list_input_devices(log_fn=log_time)

    def select_default_input_device(self):
        self.device_index = _select_default_input_device(
            current_index=self.device_index,
            log_fn=log_time,
        )

    # ---------------------------------------------------------
    # LISTENER CONTROL
    # ---------------------------------------------------------
    def start_auto_listener(self):
        if self._listener_running:
            return

        self.debug_list_input_devices()
        self.select_default_input_device()

        self._listener_running = True

        self._listener_thread = threading.Thread(
            target=self._listener_loop,
            daemon=True
        )
        self._listener_thread.start()

        log_time(f">>> [LISTENER] Thread başladı. device_index={self.device_index}")
        log_time("[DINLEME MODU] Arka plan dinlemesi aktif.")

    def stop_auto_listener(self):
        self._listener_running = False
        log_time(">>> [LISTENER] Thread durdu.")

    # ---------------------------------------------------------
    # STATE CONTROL
    # ---------------------------------------------------------
    def pause_listening(self):
        self._busy = True
        self._paused = True

    def resume_listening(self):
        self._paused = False
        self._busy = False

    # ---------------------------------------------------------
    # EVENT QUEUE
    # ---------------------------------------------------------
    def get_pending_event(self):
        if self.event_queue:
            return self.event_queue.pop(0)
        return {"type": "none"}

    # ---------------------------------------------------------
    # LISTENER LOOP
    # ---------------------------------------------------------
    def _listener_loop(self):
        recorder = PvRecorder(device_index=self.device_index, frame_length=self.frame_length)
        self.recorder = recorder
        recorder.start()

        log_time(">>> [LISTENER] PvRecorder başlatıldı.")

        collected_audio = []
        silent_frames = 0
        recording = False

        try:
            while self._listener_running:
                frame = recorder.read()

                if self._busy or self._paused:
                    collected_audio = []
                    recording = False
                    silent_frames = 0
                    continue

                audio = np.array(frame, dtype=np.float32) / 32768.0
                level = float(np.max(np.abs(audio))) if len(audio) else 0.0

                speech_detected = level > 0.02

                if speech_detected:
                    if not recording:
                        log_time(">>> [AUDIO] Ses algılandı (rolling VAD tetiklendi)...")
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
            log_time(f">>> [RECORDER ERROR] {e}")

    # ---------------------------------------------------------
    # STT PROCESS
    # ---------------------------------------------------------
    def _process_speech(self, audio_int16):
        try:
            text = self.stt_service.process_speech(audio_int16, sample_rate=16000)
        except Exception as e:
            log_time(f">>> [STT ERROR] {type(e).__name__}: {e}")
            return

        if not text or len(str(text).strip()) < 2:
            return

        if not isinstance(text, str):
            text = str(text)

        log_time(f">>> [STT] '{text}'")

        low = text.lower()

        if any(w in low for w in ["sus", "sessiz ol", "dur"]):
            self._muted = True
            self.event_queue.append({"type": "sleep"})
            return

        if self._muted and "hey" in low:
            self._muted = False
            self.event_queue.append({"type": "resumed"})
            return

        if not self._muted:
            self.event_queue.append({"type": "command", "text": text})

    # ---------------------------------------------------------
    # TTS
    # ---------------------------------------------------------
    def speak(self, text):
        if not text:
            return

        log_time(f"Poodle: {text}")
        self._tts_buffer.speak(text)

    def _speak_now(self, text):
        self.pause_listening()
        try:
            self._tts_service.speak_now(text)
        finally:
            self.resume_listening()
