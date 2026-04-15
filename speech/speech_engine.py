import threading
import time
from datetime import datetime

from faster_whisper import WhisperModel
from speech.tts_buffer import TTSBuffer
from speech.stt_service import STTService


def ts():
    return datetime.now().strftime("[%H:%M:%S.%f]")[:-3]


class PoodleSpeech:
    def __init__(self, lang="tr"):
        print(f"{ts()} >>> Modeller yükleniyor (Whisper/VAD/Piper)...")

        self.lang = lang

        # =========================
        # 🔴 CRITICAL STATE (FIX)
        # =========================
        self._speaking = False
        self._pending_phrase = None

        self._listener_running = False
        self._paused = False

        # =========================
        # 🎤 STT MODEL (CRITICAL FIX)
        # =========================
        print(f"{ts()} >>> [STT MODEL] yükleniyor...")
        self.stt_model = WhisperModel(
            "base",
            device="cpu",
            compute_type="int8"
        )
        print(f"{ts()} >>> [STT MODEL] faster_whisper hazır")

        # =========================
        # 🎧 SERVICES
        # =========================
        self.stt_service = STTService(self)
        self._tts_buffer = TTSBuffer(self)

        print(">>> [TTS INIT] mode=safe_fallback, device=None")
        print(f"{ts()} >>> [SES] Tüm sistemler hazır.")

        # =========================
        # 🎤 THREAD
        # =========================
        self._listener_thread = None

    # =========================
    # 🎤 LISTENER
    # =========================
    def start_auto_listener(self, device_index=0):
        print(f"{ts()} >>> [LISTENER] start_auto_listener entered")

        if self._listener_running:
            return

        self._listener_running = True

        self._listener_thread = threading.Thread(
            target=self._listener_loop,
            args=(device_index,),
            daemon=True
        )
        self._listener_thread.start()

    def stop_auto_listener(self):
        print(f"{ts()} >>> [LISTENER] stop_auto_listener entered")

        self._listener_running = False

        if self._listener_thread:
            self._listener_thread.join(timeout=2)

        print(f"{ts()} >>> [LISTENER] Thread durdu.")

    def _listener_loop(self, device_index):
        print(f"{ts()} >>> [LISTENER] Thread başladı. device_index={device_index}")

        try:
            from pvrecorder import PvRecorder

            recorder = PvRecorder(device_index=device_index, frame_length=512)
            recorder.start()

            print(f"{ts()} >>> [LISTENER] PvRecorder başlatıldı.")

            frames = []
            recording = False
            silence_counter = 0

            while self._listener_running:
                frame = recorder.read()
                level = max(abs(x) for x in frame)

                if level > 200:
                    recording = True
                    silence_counter = 0
                    frames.extend(frame)

                elif recording:
                    silence_counter += 1
                    frames.extend(frame)

                    if silence_counter > 10:
                        print(f"{ts()} >>> [VAD] Konuşma bitti, STT başlıyor...")
                        self._process_audio(frames)
                        frames = []
                        recording = False

                time.sleep(0.01)

        except Exception as e:
            print(f"{ts()} >>> [LISTENER ERROR] {e}")

        finally:
            try:
                recorder.stop()
                recorder.delete()
            except:
                pass

            print(f"{ts()} >>> [LISTENER] Thread durdu.")

    # =========================
    # 🎧 STT PIPELINE
    # =========================
    def _process_audio(self, frames):
        try:
            text = self.stt_service.process_speech(frames, sample_rate=16000)

            if not text:
                return

            print(f"{ts()} >>> [STT] '{text}'")

            # 🔴 BURASI SENİN PIPELINE'INDA NORMALDE DIŞARIDA
            # burada sadece fallback cevap var
            reply = self._generate_reply(text)

            self.speak(reply)

        except Exception as e:
            print(f"{ts()} >>> [STT ERROR] {e}")

    # =========================
    # 🧠 TEMP BRAIN
    # =========================
    def _generate_reply(self, text):
        text = text.lower()

        if "merhaba" in text:
            return "Selam!"
        if "nasılsın" in text:
            return "İyiyim. Sen nasılsın?"
        if "orada mısın" in text:
            return "Tabii ki buradayım."

        return "Son kısmı tam anlayamadım."

    # =========================
    # 🔊 TTS
    # =========================
    def speak(self, text):
        print(">>> [SPEAK CALL]")

        # 🔥 DOUBLE CALL ENGEL
        if self._speaking:
            print(">>> [SPEAK BLOCKED]")
            return

        # 🔥 AYNI CÜMLE ENGEL
        if self._pending_phrase == text:
            print(">>> [DUPLICATE BLOCKED]")
            return

        self._speaking = True
        self._pending_phrase = text

        try:
            print(f"Poodle: {text}")
            self._tts_buffer.speak(text)

        except Exception as e:
            print(f">>> [TTS ERROR] {e}")

        finally:
            self._speaking = False
            self._pending_phrase = None
