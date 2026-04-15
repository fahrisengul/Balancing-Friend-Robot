import threading
from datetime import datetime
from pathlib import Path

from faster_whisper import WhisperModel
from piper.voice import PiperVoice
from silero_vad import load_silero_vad

from .audio_devices import debug_list_input_devices, select_default_input_device
from .vad_listener import RollingVADListener
from .stt_service import STTService
from .tts_service import TTSService
from .tts_buffer import TTSBuffer


class PoodleSpeech:
    DEBUG_AUDIO = False

    def __init__(self, lang: str = "tr", input_device_index=None):
        self.lang = lang
        self.frame_length = 512
        self.sample_rate = 16000

        self.event_queue = []

        self._listener_running = False
        self._busy = False
        self._muted = False

        self.recorder = None
        self.listener_thread = None
        self._recorder_lock = threading.Lock()

        self.device_index = input_device_index

        self._pending_phrase = ""
        self._pending_phrase_since = 0.0
        self._min_phrase_chars = 28
        self._max_phrase_wait_sec = 0.7
        self._last_tts_time = 0.0
        self._tts_cooldown_sec = 0.65

        self.log_time(">>> Modeller yükleniyor (Whisper/VAD/Piper)...")
        self.stt_model = WhisperModel("base", device="cpu", compute_type="int8")
        self.vad_model = load_silero_vad()
        project_root = Path(__file__).resolve().parents[1]
        model_path = project_root / "models" / "tr_TR-fahrettin-medium.onnx"
        self.voice = PiperVoice.load(str(model_path))
        self.log_time(">>> [SES] Tüm sistemler hazır.")
        self._vad_listener = RollingVADListener(self)
        self._stt_service = STTService(self)
        self._tts_service = TTSService(self)
        self._tts_buffer = TTSBuffer(self)

    @staticmethod
    def get_now():
        return datetime.now().strftime("%H:%M:%S.%f")[:-3]

    def log_time(self, message: str):
        print(f"[{self.get_now()}] {message}")

    # =========================================================
    # DEVICE / DEBUG
    # =========================================================
    def debug_list_input_devices(self):
        debug_list_input_devices(self.log_time)

    def select_default_input_device(self):
        self.device_index = select_default_input_device(self.device_index, self.log_time)
        return self.device_index

    # =========================================================
    # STATE
    # =========================================================
    def is_muted(self):
        return self._muted

    def set_busy(self, val: bool):
        self._busy = val

    # =========================================================
    # AUTO LISTENER
    # =========================================================
    def start_auto_listener(self):
        if self._listener_running:
            return

        if self.device_index is None or self.device_index < 0:
            self.select_default_input_device()

        self._listener_running = True
        self.listener_thread = threading.Thread(target=self._listener_loop, daemon=True)
        self.listener_thread.start()
        self.log_time("[DINLEME MODU] Arka plan dinlemesi aktif.")

    def stop_auto_listener(self):
        self._listener_running = False

        if self.listener_thread and self.listener_thread.is_alive():
            self.listener_thread.join(timeout=2.0)

        recorder_to_cleanup = None
        with self._recorder_lock:
            if self.recorder is not None:
                recorder_to_cleanup = self.recorder
                self.recorder = None

        if recorder_to_cleanup is not None:
            try:
                recorder_to_cleanup.stop()
            except Exception:
                pass

            try:
                recorder_to_cleanup.delete()
            except Exception:
                pass

        self.listener_thread = None

    def get_pending_event(self):
        if len(self.event_queue) > 0:
            return self.event_queue.pop(0)
        return {"type": "none"}

    # =========================================================
    # DELEGATED INTERNALS
    # =========================================================
    def _listener_loop(self):
        self._vad_listener.listener_loop()

    def _process_speech(self, audio_int16):
        self._stt_service.process_speech(audio_int16)

    def _speak_now(self, text):
        self._tts_service.speak_now(text)

    def speak(self, text):
        self._tts_buffer.speak(text)

    def flush_pending_tts(self):
        self._tts_buffer.flush_pending_tts()
