import os
import subprocess
import tempfile
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

            import pyaudio  # dependency kontrolü
            self.microphone = sr.Microphone()

            print(">>> [SES] Poodle kulağını açtı, ses motoru sıcak ve hazır!")

        except Exception as e:
            print(f">>> [HATA] Başlatma hatası: {e}")

    def speak(self, text):
        if not text:
            return

        if not self.voice:
            print(">>> [SES HATASI] Piper voice yüklenemedi.")
            return

        print(f"Poodle: {text}")
        temp_path = None

        try:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
                temp_path = tmp_file.name

            # Piper'ın WAV çıktısını doğrudan binary dosyaya yazdır
            with open(temp_path, "wb") as raw_file:
                self.voice.synthesize(text, raw_file)

            if not os.path.exists(temp_path):
                raise RuntimeError("TTS çıktı dosyası oluşturulamadı.")

            result = subprocess.run(
                ["/usr/bin/afplay", temp_path],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                text=True
            )

            if result.returncode != 0:
                raise RuntimeError(result.stderr.strip() or "afplay başarısız oldu.")

        except Exception as e:
            print(f">>> [SES HATASI] {e}")

        finally:
            if temp_path and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
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
