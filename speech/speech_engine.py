import os
import platform
import tempfile
import threading
import time
import wave

import numpy as np
import torch
from pvrecorder import PvRecorder

from .audio_devices import debug_list_input_devices, select_default_input_device
from .stt_service import STTService
from .tts_buffer import TTSBuffer
from .tts_service import TTSService


def log_time(message: str):
    now = time.strftime("%H:%M:%S")
    ms = int((time.time() % 1) * 1000)
    print(f"[{now}.{ms:03d}] {message}")


class PoodleSpeech:
    def __init__(self, input_device_index=-1, lang="tr"):
        self.lang = lang
        self.frame_length = 512
        self.device_index = input_device_index
        self.event_queue = []

        self._listener_running = False
        self._busy = False
        self._muted = False
        self._paused = False
        self._listener_thread = None
        self.recorder = None

        log_time(">>> Modeller yükleniyor (Whisper/VAD/Piper)...")

        self.stt_service = STTService(self)
            try:
                self.stt_service = STTService(self)
            except TypeError:
                try:
                    self.stt_service = STTService(lang=self.lang)
                except TypeError:
        self.stt_service = STTService()
        self._tts_service = TTSService(self)
        self._tts_buffer = TTSBuffer(self)

        log_time(">>> [SES] Tüm sistemler hazır.")

        debug_list_input_devices(log_fn=log_time)
        self.device_index = select_default_input_device(
            current_index=self.device_index,
            log_fn=log_time,
        )

    # ---------------------------------------------------------
    # Listener control
    # ---------------------------------------------------------
    def start_auto_listener(self):
        if self._listener_running:
            return

        self._listener_running = True
        self._listener_thread = threading.Thread(
            target=self._listener_loop,
            daemon=True,
        )
        self._listener_thread.start()
        log_time(f">>> [LISTENER] Thread başladı. device_index={self.device_index}")
        log_time("[DINLEME MODU] Arka plan dinlemesi aktif.")

    def stop_auto_listener(self):
        self._listener_running = False
        if self._listener_thread and self._listener_thread.is_alive():
            self._listener_thread.join(timeout=1.0)
        log_time(">>> [LISTENER] Thread durdu.")

    def pause_listening(self):
        self._busy = True
        self._paused = True

    def resume_listening(self):
        self._paused = False
        self._busy = False

    # ---------------------------------------------------------
    # Event queue
    # ---------------------------------------------------------
    def get_pending_event(self):
        if self.event_queue:
            return self.event_queue.pop(0)
        return {"type": "none"}

    # ---------------------------------------------------------
    # Core listener loop
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

                audio_float32 = np.array(frame, dtype=np.float32) / 32768.0

                # Basit seviye tabanlı tetikleme; mevcut rolling VAD akışına sadık
                level = float(np.max(np.abs(audio_float32))) if len(audio_float32) else 0.0
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
            log_time(f">>> [RECORDER ERROR] {type(e).__name__}: {e}")

        finally:
            try:
                recorder.stop()
            except Exception:
                pass
            try:
                recorder.delete()
            except Exception:
                pass

    # ---------------------------------------------------------
    # STT
    # ---------------------------------------------------------
    def _process_speech(self, audio_int16):
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp_path = tmp.name

        with wave.open(tmp_path, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(16000)
            wf.writeframes(audio_int16.tobytes())

        try:
            text = self.stt_service.transcribe_file(tmp_path)
        finally:
            try:
                os.remove(tmp_path)
            except Exception:
                pass

        if not text or len(text.strip()) < 2:
            return

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
            self.event_queue.append({"type": "command", "text": text})

    # ---------------------------------------------------------
    # TTS
    # ---------------------------------------------------------
    def _speak_now(self, text):
        self.pause_listening()
        try:
            self._tts_service.speak_now(text)
        finally:
            self.resume_listening()

    def speak(self, text):
        if not text:
            return

        log_time(f"Poodle: {text}")
        self._tts_buffer.speak(text)
