import threading
import time
import traceback
from datetime import datetime

import numpy as np
from pvrecorder import PvRecorder
from faster_whisper import WhisperModel

from .audio_devices import (
    debug_list_input_devices as _debug_list_input_devices,
    select_default_input_device as _select_default_input_device,
)
from .stt_service import STTService
from .tts_buffer import TTSBuffer
from .tts_service import TTSService


def get_now():
    return datetime.now().strftime("%H:%M:%S.%f")[:-3]


def log_time(message):
    print(f"[{get_now()}] {message}")


class PoodleSpeech:
    def __init__(self, lang="tr", input_device_index=0):
        self.lang = lang
        self.frame_length = 512
        self.input_samplerate = 16000
        self.event_queue = []

        self._listener_running = False
        self._listener_thread = None
        self._busy = False
        self._paused = False
        self._muted = False

        self.device_index = input_device_index
        self.recorder = None
        self._loop_counter = 0

        log_time(">>> Modeller yükleniyor (Whisper/VAD/Piper)...")

        try:
            self.stt_model = WhisperModel("base", device="cpu", compute_type="int8")
            log_time(">>> [STT MODEL] faster_whisper hazır")
        except Exception as e:
            log_time(f">>> [STT MODEL ERROR] {type(e).__name__}: {e}")
            traceback.print_exc()
            raise

        self.stt_service = STTService(self)
        self._tts_service = TTSService(self)
        self._tts_buffer = TTSBuffer(self)

        log_time(">>> [SES] Tüm sistemler hazır.")

    # ---------------------------------------------------------
    # Compatibility wrappers
    # ---------------------------------------------------------
    def debug_list_input_devices(self):
        log_time(">>> [MIC DEBUG] Listing input devices...")
        _debug_list_input_devices(log_fn=log_time)

    def select_default_input_device(self):
        old_index = self.device_index
        self.device_index = _select_default_input_device(
            current_index=self.device_index,
            log_fn=log_time,
        )
        log_time(f">>> [MIC SELECT] old_index={old_index} new_index={self.device_index}")
        return self.device_index

    # ---------------------------------------------------------
    # State control
    # ---------------------------------------------------------
    def is_muted(self):
        return self._muted

    def set_busy(self, value: bool):
        self._busy = bool(value)
        log_time(f">>> [STATE] busy={self._busy}")

    def pause_listening(self):
        self._busy = True
        self._paused = True
        log_time(">>> [STATE] listening paused")

    def resume_listening(self):
        self._paused = False
        self._busy = False
        log_time(">>> [STATE] listening resumed")

    # ---------------------------------------------------------
    # Queue
    # ---------------------------------------------------------
    def get_pending_event(self):
        if self.event_queue:
            evt = self.event_queue.pop(0)
            log_time(f">>> [QUEUE] pop event={evt}")
            return evt
        return {"type": "none"}

    # ---------------------------------------------------------
    # Listener lifecycle
    # ---------------------------------------------------------
    def start_auto_listener(self):
        log_time(">>> [LISTENER] start_auto_listener entered")

        if self._listener_running:
            log_time(">>> [LISTENER] already running, skip")
            return

        self.debug_list_input_devices()
        self.select_default_input_device()

        self._listener_running = True
        self._listener_thread = threading.Thread(
            target=self._listener_loop,
            daemon=True,
            name="PoodleListenerThread",
        )
        self._listener_thread.start()

        log_time(f">>> [LISTENER] Thread başladı. device_index={self.device_index}")
        log_time("[DINLEME MODU] Arka plan dinlemesi aktif.")

    def stop_auto_listener(self):
        log_time(">>> [LISTENER] stop_auto_listener entered")
        self._listener_running = False

        thread = self._listener_thread
        if thread and thread.is_alive():
            log_time(">>> [LISTENER] joining listener thread...")
            thread.join(timeout=2.0)
            log_time(f">>> [LISTENER] thread alive after join? {thread.is_alive()}")

        log_time(">>> [LISTENER] Thread durdu.")

    # ---------------------------------------------------------
    # Listener loop
    # ---------------------------------------------------------
    def _listener_loop(self):
        log_time(">>> [LISTENER LOOP] entered")

        recorder = None
        try:
            log_time(f">>> [LISTENER LOOP] creating PvRecorder for device_index={self.device_index}")
            recorder = PvRecorder(device_index=self.device_index, frame_length=self.frame_length)
            self.recorder = recorder

            log_time(">>> [LISTENER LOOP] calling recorder.start()")
            recorder.start()
            log_time(">>> [LISTENER] PvRecorder başlatıldı.")

            collected_audio = []
            silent_frames = 0
            recording = False

            start_threshold = 0.006
            continue_threshold = 0.004
            max_silence_frames = 25

            while self._listener_running:
                self._loop_counter += 1

                frame = recorder.read()

                if self._loop_counter % 100 == 0:
                    log_time(
                        f">>> [LISTENER LOOP] alive loop={self._loop_counter}, "
                        f"busy={self._busy}, paused={self._paused}, recording={recording}"
                    )

                if self._busy or self._paused:
                    collected_audio = []
                    recording = False
                    silent_frames = 0
                    continue

                audio_float32 = np.array(frame, dtype=np.float32) / 32768.0
                rms = float(np.sqrt(np.mean(np.square(audio_float32)))) if len(audio_float32) else 0.0

                if rms > 0.002:
                    log_time(f">>> [MIC LEVEL] rms={rms:.4f}")

                if not recording:
                    if rms >= start_threshold:
                        log_time(">>> [AUDIO] Ses algılandı...")
                        recording = True
                        collected_audio.extend(frame)
                        silent_frames = 0
                else:
                    collected_audio.extend(frame)

                    if rms >= continue_threshold:
                        silent_frames = 0
                    else:
                        silent_frames += 1

                    if silent_frames > max_silence_frames:
                        log_time(">>> [VAD] Konuşma bitti, STT başlıyor...")

                        audio_data = np.array(collected_audio, dtype=np.int16)

                        threading.Thread(
                            target=self._process_speech,
                            args=(audio_data,),
                            daemon=True,
                            name="PoodleSTTThread",
                        ).start()

                        collected_audio = []
                        recording = False
                        silent_frames = 0

            log_time(">>> [LISTENER LOOP] while loop exited because _listener_running=False")

        except Exception as e:
            log_time(f">>> [LISTENER CRASH] {type(e).__name__}: {e}")
            traceback.print_exc()

        finally:
            log_time(">>> [LISTENER LOOP] finally entered")
            try:
                if recorder is not None:
                    log_time(">>> [LISTENER LOOP] recorder.stop()")
                    recorder.stop()
            except Exception as e:
                log_time(f">>> [LISTENER LOOP STOP ERROR] {type(e).__name__}: {e}")

            try:
                if recorder is not None:
                    log_time(">>> [LISTENER LOOP] recorder.delete()")
                    recorder.delete()
            except Exception as e:
                log_time(f">>> [LISTENER LOOP DELETE ERROR] {type(e).__name__}: {e}")

            self.recorder = None
            log_time(">>> [LISTENER LOOP] finally completed")

    # ---------------------------------------------------------
    # STT
    # ---------------------------------------------------------
    def _process_speech(self, audio_int16):
        log_time(">>> [STT PIPELINE] _process_speech entered")
        try:
            text = self.stt_service.process_speech(
                audio_int16,
                sample_rate=self.input_samplerate,
            )
        except Exception as e:
            log_time(f">>> [STT ERROR] {type(e).__name__}: {e}")
            traceback.print_exc()
            return

        if not text or len(str(text).strip()) < 2:
            log_time(">>> [STT PIPELINE] empty/short text, skip")
            return

        if not isinstance(text, str):
            text = str(text)

        log_time(f">>> [STT] '{text}'")

        low = text.lower()

        if any(w in low for w in ["sus", "sessiz ol", "dur"]):
            self._muted = True
            log_time(">>> [MODE] Sessiz mod.")
            self.event_queue.append({"type": "sleep"})
            return

        if self._muted and "hey" in low:
            self._muted = False
            log_time(">>> [MODE] Aktif mod.")
            self.event_queue.append({"type": "resumed"})
            return

        if not self._muted:
            evt = {"type": "command", "text": text}
            self.event_queue.append(evt)
            log_time(f">>> [QUEUE] push event={evt}")

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
            time.sleep(0.3)
            self.resume_listening()
