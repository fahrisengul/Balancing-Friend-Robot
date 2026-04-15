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
    def __init__(self, lang="tr", input_device_index=0):
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
    # CORE LOOP (SAFE VERSION)
    # ---------------------------------------------------------
    def _listener_loop(self):
        try:
            recorder = PvRecorder(
                device_index=self.device_index,
                frame_length=self.frame_length
            )
            self.recorder = recorder
            recorder.start()

            log_time(">>> [LISTENER] PvRecorder başlatıldı.")

            while self._listener_running:
                frame = recorder.read()

                audio_float32 = np.array(frame, dtype=np.float32) / 32768.0
                level = float(np.max(np.abs(audio_float32)))

                # DEBUG
                if level > 0.002:
                    log_time(f">>> [MIC LEVEL] {level:.4f}")

        except Exception as e:
            log_time(f">>> [LISTENER CRASH] {type(e).__name__}: {e}")
