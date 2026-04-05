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
    if not text:
        print(">>> [DEBUG] speak() boş text aldı.")
        return

    if not self.voice:
        print(">>> [SES HATASI] Piper voice yüklenemedi.")
        return

    print(f"Poodle: {text}")

    filename = os.path.abspath("poodle_voice.wav")
    print(f">>> [DEBUG] WAV PATH: {filename}")

    try:
        # Eski dosya varsa temizle
        if os.path.exists(filename):
            os.remove(filename)

        print(">>> [DEBUG] wave.open başlıyor...")
        with wave.open(filename, "wb") as wav_file:
            print(">>> [DEBUG] synthesize_wav çağrılıyor...")
            result = self.voice.synthesize_wav(text, wav_file)
            print(f">>> [DEBUG] synthesize_wav tamamlandı. result={result}")

        print(">>> [DEBUG] wave dosyası kapandı.")

        if not os.path.exists(filename):
            raise RuntimeError("WAV dosyası hiç oluşmadı.")

        size = os.path.getsize(filename)
        print(f">>> [DEBUG] WAV SIZE: {size} byte")

        if size == 0:
            raise RuntimeError("WAV dosyası oluştu ama boş kaldı.")

        result = subprocess.run(
            ["/usr/bin/afplay", filename],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True
        )

        print(f">>> [DEBUG] afplay returncode={result.returncode}")

        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or "afplay başarısız oldu.")

    except Exception as e:
        print(f">>> [SES HATASI] {type(e).__name__}: {e}")

    def listen(self):
        if not self.microphone:
            return None

        finally:
            # if temp_path and os.path.exists(temp_path):
            #    try:
            #        os.remove(temp_path)
                except Exception:
                    pass

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
