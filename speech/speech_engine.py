import threading
import time
from datetime import datetime

from faster_whisper import WhisperModel
from speech.tts_buffer import TTSBuffer
from speech.stt_service import STTService


def ts():
    return datetime.now().strftime("[%H:%M:%S.%f]")[:-3]


class PoodleSpeech:
    def __init__(self):
        print(">>> Modeller yükleniyor (Whisper/VAD/Piper)...")

        # -------------------------
        # STATE
        # -------------------------
        self._speaking = False

        # -------------------------
        # STT MODEL
        # -------------------------
        from faster_whisper import WhisperModel

        print(">>> [STT MODEL] yükleniyor...")
        self.stt_model = WhisperModel("base", compute_type="int8")
        print(">>> [STT MODEL] faster_whisper hazır")

        # -------------------------
        # TTS ENGINE (GARANTİ)
        # -------------------------
        import pyttsx3

        self._engine = pyttsx3.init()
        self._engine.setProperty("rate", 180)

        # -------------------------
        # SERVICES
        # -------------------------
        from speech.stt_service import STTService
        from speech.tts_buffer import TTSBuffer

        self.stt_service = STTService(self)
        self._tts_buffer = TTSBuffer(self)

        print(">>> [SES] Tüm sistemler hazır.")

    # =========================================================
    # PUBLIC SPEAK
    # =========================================================
    def speak(self, text):
        print(">>> [SPEAK CALL]")
        print(f"Poodle: {text}")

        self._tts_buffer.speak(text)

    # =========================================================
    # INTERNAL SPEAK (BUFFER ÇAĞIRIR)
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
    # LISTENER CONTROL (GERİ EKLENDİ)
    # =========================================================
    def start_auto_listener(self, device_index=0):
        print(">>> [LISTENER] start_auto_listener entered")
    
        import threading
        import pvrecorder
    
        self._listener_running = True
        self._device_index = device_index
    
        def _loop():
            print(f">>> [LISTENER] Thread başladı. device_index={device_index}")
    
            recorder = None
    
            try:
                recorder = pvrecorder.PvRecorder(device_index=device_index, frame_length=512)
                recorder.start()
                print(">>> [LISTENER] PvRecorder başlatıldı.")
    
                while self._listener_running:
                    pcm = recorder.read()
    
                    # STT pipeline
                    self.stt_service.process_audio_chunk(pcm)
    
            except Exception as e:
                print(f">>> [LISTENER ERROR] {e}")
    
            finally:
                if recorder:
                    try:
                        recorder.stop()
                        recorder.delete()
                    except:
                        pass
    
                print(">>> [LISTENER] Thread durdu.")
    
        self._listener_thread = threading.Thread(target=_loop, daemon=True)
        self._listener_thread.start()
    
    
    def stop_auto_listener(self):
        print(">>> [LISTENER] stop_auto_listener entered")
    
        self._listener_running = False
    
        if hasattr(self, "_listener_thread"):
            self._listener_thread.join(timeout=2)
    
        print(">>> [LISTENER] Thread durdu.")
