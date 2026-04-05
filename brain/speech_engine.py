import os
import wave
import subprocess
import speech_recognition as sr
from piper.voice import PiperVoice


class PoodleSpeech:
    def __init__(self, lang="tr-TR"):
        self.recognizer = sr.Recognizer()
        self.lang = lang
        self.voice = None
        self.microphone = None

        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.model_path = os.path.join(current_dir, "tr_TR-fahrettin-medium.onnx")

        try:
            print(">>> Piper modeli belleğe yükleniyor (Lütfen bekleyin)...")

            if not os.path.exists(self.model_path):
                raise FileNotFoundError(f"Model bulunamadı: {self.model_path}")

            self.voice = PiperVoice.load(self.model_path)

            import pyaudio
            self.microphone = sr.Microphone()

            print(">>> [SES] Poodle kulağını açtı, ses motoru sıcak ve hazır!")

        except Exception as e:
            print(f">>> [HATA] Başlatma hatası: {e}")

    def speak(self, text):
        if not text or not self.voice:
            return

        print(f"Poodle: {text}")
        filename = "poodle_voice.wav"

        try:
            with wave.open(filename, "wb") as wav_file:
                # KRITIK: synthesize DEGIL, synthesize_wav kullan
                self.voice.synthesize_wav(text, wav_file)

            if not os.path.exists(filename) or os.path.getsize(filename) == 0:
                raise RuntimeError("WAV dosyası oluşmadı veya boş.")

            result = subprocess.run(
                ["/usr/bin/afplay", filename],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                text=True
            )

            if result.returncode != 0:
                raise RuntimeError(result.stderr.strip() or "afplay başarısız oldu.")

        except Exception as e:
            print(f">>> [SES HATASI] {e}")

        finally:
            if os.path.exists(filename):
                try:
                    os.remove(filename)
                except Exception:
                    pass

    def listen(self):
        if not self.microphone:
            return None

        with self.microphone as source:
            print("\n[Dinleniyor...] Poodle seni duymaya hazır...")
            try:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.2)
                audio = self.recognizer.listen(source, timeout=4, phrase_time_limit=6)
                text = self.recognizer.recognize_google(audio, language=self.lang)
                print(f"Tanem: {text}")
                return text.lower()

            except sr.WaitTimeoutError:
                return None
            except sr.UnknownValueError:
                return None
            except sr.RequestError as e:
                print(f">>> [DINLEME HATASI] Google STT erişim hatası: {e}")
                return None
            except Exception as e:
                print(f">>> [DINLEME HATASI] {e}")
                return None
