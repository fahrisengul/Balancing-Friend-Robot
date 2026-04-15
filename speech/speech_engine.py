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
    def start_auto_listener(self, device_index=0):
        print(f"{ts()} >>> [LISTENER] start_auto_listener entered")

        if self._listener_running:
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

            start_threshold = 200
            continue_threshold = 120
            silence_limit = 12

            while self._listener_running:
                pcm = recorder.read()

                level = max(abs(x) for x in pcm)

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

                time.sleep(0.01)

        except Exception as e:
            print(f"{ts()} >>> [LISTENER ERROR] {e}")

        finally:
            if recorder:
                recorder.stop()
                recorder.delete()

            print(f"{ts()} >>> [LISTENER] Thread durdu.")

    # =========================================================
    def _process_audio(self, frames):
        try:
            text = self.stt_service.process_speech(frames, sample_rate=16000)

            if not text:
                return

            print(f"{ts()} >>> [STT] '{text}'")

            reply = self._generate_reply(text)
            self.speak(reply)

        except Exception as e:
            print(f"{ts()} >>> [STT ERROR] {e}")

    # =========================================================
    # 🔥 GELİŞTİRİLMİŞ REPLY LOGIC
    # =========================================================
    def _generate_reply(self, text):
        low = text.lower().strip()

        # normalize
        low = low.replace(".", "").replace(",", "").replace("?", "")

        # selam varyasyonları
        if any(x in low for x in ["merhaba", "selam", "slm", "hello"]):
            return "Selam!"

        # nasılsın varyasyonları
        if any(x in low for x in ["nasılsın", "naber", "iyi misin"]):
            return "İyiyim. Sen nasılsın?"

        # teşekkür varyasyonları
        if any(x in low for x in ["teşekkür", "sağ ol", "thanks"]):
            return "Rica ederim."

        # rica ederim yakala (karşılıklı diyalog)
        if "rica ederim" in low:
            return "Ne demek, her zaman."

        # orada mısın
        if "orada mısın" in low:
            return "Buradayım."

        # kullanıcı zaten anlamadım diyorsa loop’a girme
        if "anlamadım" in low:
            return "Daha net söyleyebilir misin?"

        # fallback
        return "Son kısmı tam anlayamadım."
