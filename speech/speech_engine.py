import threading
import time
from datetime import datetime

import numpy as np
from faster_whisper import WhisperModel
from speech.tts_buffer import TTSBuffer
from speech.stt_service import STTService


def ts():
    return datetime.now().strftime("[%H:%M:%S.%f]")[:-3] + "]"


class PoodleSpeech:
    def __init__(self, lang="tr"):
        print(f"{ts()} >>> Modeller yükleniyor (Whisper/VAD/Piper)...")

        self.lang = lang

        # STATE
        self._speaking = False
        self._listener_running = False
        self._listener_thread = None
        self._device_index = 0
        self._pending_phrase = None

        # STT
        print(f"{ts()} >>> [STT MODEL] yükleniyor...")
        self.stt_model = WhisperModel("base", compute_type="int8")
        print(f"{ts()} >>> [STT MODEL] faster_whisper hazır")

        # TTS
        import pyttsx3
        self._engine = pyttsx3.init()
        self._engine.setProperty("rate", 180)

        # SERVICES
        self.stt_service = STTService(self)
        self._tts_buffer = TTSBuffer(self)

        print(f"{ts()} >>> [SES] Tüm sistemler hazır.")

    # =========================================================
    def speak(self, text):
        print(">>> [SPEAK CALL]")

        if not text:
            return

        print(f"Poodle: {text}")
        self._tts_buffer.speak(text)

    # =========================================================
    def _speak_now(self, text):
        try:
            self._speaking = True
            print(">>> [TTS START]")
            self._engine.say(text)
            self._engine.runAndWait()
            print(">>> [TTS END]")
        except Exception as e:
            print(f">>> [TTS ERROR] {e}")
        finally:
            self._speaking = False

    # =========================================================
    # LISTENER CONTROL
    # =========================================================
    def start_auto_listener(self, device_index=0):
        print(f"{ts()} >>> [LISTENER] start_auto_listener entered")

        if self._listener_running:
            print(f"{ts()} >>> [LISTENER] already running")
            return

        self._listener_running = True
        self._device_index = device_index

        self._listener_thread = threading.Thread(
            target=self._listener_loop,
            args=(device_index,),
            daemon=True
        )
        self._listener_thread.start()

        print(f"{ts()} >>> [LISTENER] Thread başladı. device_index={device_index}")

    def stop_auto_listener(self):
        print(f"{ts()} >>> [LISTENER] stop_auto_listener entered")

        self._listener_running = False

        if self._listener_thread:
            self._listener_thread.join(timeout=2)

        print(f"{ts()} >>> [LISTENER] Thread durdu.")

    # =========================================================
    # LISTENER LOOP
    # =========================================================
    def _listener_loop(self, device_index):
        recorder = None

        try:
            from pvrecorder import PvRecorder

            recorder = PvRecorder(device_index=device_index, frame_length=512)
            recorder.start()

            print(f"{ts()} >>> [LISTENER] PvRecorder başlatıldı.")

            frames = []
            recording = False
            silence_counter = 0

            # 🔧 TUNED VALUES
            start_threshold = 200
            continue_threshold = 120
            silence_limit = 6   # 🔥 12 → 6 (kritik fix)

            while self._listener_running:
                pcm = recorder.read()

                try:
                    level = max(abs(x) for x in pcm)
                except ValueError:
                    level = 0

                if not recording and level > start_threshold:
                    recording = True
                    silence_counter = 0
                    frames.extend(pcm)

                elif recording:
                    frames.extend(pcm)

                    if level > continue_threshold:
                        silence_counter = 0
                    else:
                        silence_counter += 1

                    if silence_counter > silence_limit:
                        print(f"{ts()} >>> [VAD] Konuşma bitti, STT başlıyor...")
                        self._process_audio(frames)

                        frames = []
                        recording = False
                        silence_counter = 0

        except Exception as e:
            print(f">>> [LISTENER ERROR] {e}")

        finally:
            if recorder:
                recorder.stop()
                recorder.delete()

    # =========================================================
    # AUDIO PROCESS
    # =========================================================
    def _process_audio(self, frames):
        try:
            text = self.stt_service.process_speech(frames)

            print(f"{ts()} >>> [STT] '{text}'")

            if not text:
                return

            # 🔥 CLEAN TEXT
            text = text.strip().lower()

            # 🔥 NOISE FILTER
            if len(text) < 3:
                return

            # 🔥 BAD STT FILTER
            if any(x in text for x in ["sum kısmı", "çamaran", "yamadı"]):
                return

            reply = self._generate_reply(text)

            if reply:
                self.speak(reply)

        except Exception as e:
            print(f">>> [PROCESS ERROR] {e}")

    # =========================================================
    # 🔥 NEW REPLY ENGINE (KRİTİK)
    # =========================================================
    def _generate_reply(self, text):
        # normalize
        t = text.lower().strip()

        # greeting
        if any(x in t for x in ["merhaba", "selam", "mahaba"]):
            return "Selam!"

        # nasılsın
        if "nasılsın" in t:
            return "İyiyim. Sen nasılsın?"

        # teşekkür
        if "teşekkür" in t:
            return "Rica ederim."

        # aynalama (mirror)
        if len(t) > 5 and len(t) < 40:
            return t.capitalize()

        # 🔥 fallback (ama spam değil!)
        if len(t) < 6:
            return None

        return "Tam anlayamadım, tekrar söyler misin?"
