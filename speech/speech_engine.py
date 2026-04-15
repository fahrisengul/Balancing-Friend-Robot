import threading
import time
from datetime import datetime

import numpy as np
from pvrecorder import PvRecorder

from .stt_service import STTService
from .tts_service import TTSService
from .tts_buffer import TTSBuffer


def get_now():
    return datetime.now().strftime("%H:%M:%S.%f")[:-3]


def log_time(message):
    print(f"[{get_now()}] {message}")


class PoodleSpeech:
    def __init__(self, brain=None, lang="tr", input_device_index=0):
        self.brain = brain
        self.lang = lang

        self.frame_length = 512
        self.input_samplerate = 16000

        self.device_index = input_device_index

        self._listener_running = False
        self._busy = False
        self._paused = False

        self._listener_thread = None
        self.recorder = None

        log_time(">>> Modeller yükleniyor (Whisper/VAD/Piper)...")

        # Whisper model (owner üzerinden STTService kullanacak)
        from faster_whisper import WhisperModel
        self.stt_model = WhisperModel("base", device="cpu", compute_type="int8")

        self.stt_service = STTService(self)

        self._tts_service = TTSService(self)
        self._tts_buffer = TTSBuffer(self)

        log_time(">>> [SES] Tüm sistemler hazır.")

    # ---------------------------------------------------------
    # LISTENER CONTROL
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

        if self.recorder:
            try:
                self.recorder.stop()
            except Exception:
                pass

        if self._listener_thread and self._listener_thread.is_alive():
            self._listener_thread.join(timeout=1.0)

        log_time(">>> [LISTENER] Thread durdu.")

    # ---------------------------------------------------------
    # LISTENER LOOP (FIXED)
    # ---------------------------------------------------------
    def _listener_loop(self):
        recorder = PvRecorder(
            device_index=self.device_index,
            frame_length=self.frame_length,
        )
        self.recorder = recorder
        recorder.start()

        log_time(">>> [LISTENER] PvRecorder başlatıldı.")

        collected_audio = []
        silent_frames = 0
        recording = False

        # 🔥 SENİN ORTAMINA UYGUN EŞİKLER
        start_threshold = 0.006
        continue_threshold = 0.004
        max_silence_frames = 25

        try:
            while self._listener_running:
                frame = recorder.read()

                if self._busy or self._paused:
                    collected_audio = []
                    recording = False
                    silent_frames = 0
                    continue

                audio_float32 = np.array(frame, dtype=np.float32) / 32768.0

                # RMS hesap
                rms = float(np.sqrt(np.mean(np.square(audio_float32))))

                # Debug (istersen kaldır)
                if rms > 0.002:
                    log_time(f">>> [MIC LEVEL] {rms:.4f}")

                # ----------------------
                # START DETECTION
                # ----------------------
                if not recording:
                    if rms >= start_threshold:
                        log_time(">>> [AUDIO] Ses algılandı...")
                        recording = True
                        collected_audio.extend(frame)
                        silent_frames = 0

                # ----------------------
                # RECORDING
                # ----------------------
                else:
                    collected_audio.extend(frame)

                    if rms >= continue_threshold:
                        silent_frames = 0
                    else:
                        silent_frames += 1

                    # ----------------------
                    # END DETECTION
                    # ----------------------
                    if silent_frames > max_silence_frames:
                        log_time(">>> [VAD] Konuşma bitti, STT başlıyor...")

                        audio_data = np.array(collected_audio, dtype=np.int16)

                        threading.Thread(
                            target=self._process_speech,
                            args=(audio_data,),
                            daemon=True,
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
    # STT → BRAIN → TTS
    # ---------------------------------------------------------
    def _process_speech(self, audio_int16):
        try:
            text = self.stt_service.process_speech(
                audio_int16,
                sample_rate=self.input_samplerate,
            )
        except Exception as e:
            log_time(f">>> [STT ERROR] {type(e).__name__}: {e}")
            return

        if not text or len(text.strip()) < 2:
            return

        log_time(f">>> [STT] '{text}'")

        # Brain
        if self.brain:
            try:
                reply = self.brain.ask_poodle(text)
            except Exception:
                reply = "Anlayamadım."
        else:
            reply = "Anladım."

        log_time(f">>> [POODLE] {reply}")

        # Speak
        self._speak_now(reply)

    # ---------------------------------------------------------
    # TTS
    # ---------------------------------------------------------
    def speak(self, text):
        if not text:
            return
        log_time(f"Poodle: {text}")
        self._tts_buffer.speak(text)

    def _speak_now(self, text):
        self._busy = True
        try:
            self._tts_service.speak_now(text)
        finally:
            time.sleep(0.3)
            self._busy = False
