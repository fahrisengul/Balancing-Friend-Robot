import os
import time
import speech_recognition as sr
from gtts import gTTS
from playsound import playsound

class PoodleSpeech:
    def __init__(self, lang="tr-TR"):
        self.recognizer = sr.Recognizer()
        self.lang = lang
        self.microphone = None
        
        # --- HASSAS KULAK AYARLARI ---
        self.recognizer.energy_threshold = 300    # Ses tetikleme seviyesi
        self.recognizer.dynamic_energy_threshold = True # Ortama göre kendini ayarlar
        self.recognizer.pause_threshold = 0.8     # Konuşma bittiğini anlamak için bekleme
        
        try:
            import pyaudio
            self.microphone = sr.Microphone()
            with self.microphone as source:
                print(">>> [SES] Ortam gürültüsü kalibre ediliyor (1sn)...")
                # Odayı 1 saniye dinleyip gürültüyü profiller
                self.recognizer.adjust_for_ambient_noise(source, duration=1.0)
            print(">>> [SES] Mikrofon başarıyla bağlandı ve kalibre edildi.")
        except (ImportError, AttributeError, Exception) as e:
            print(f">>> [UYARI] Mikrofon sorunu: {e}")

    def speak(self, text):
        if not text: return
        print(f"Poodle: {text}")
        try:
            tts = gTTS(text=text, lang="tr")
            filename = "temp_voice.mp3"
            tts.save(filename)
            playsound(filename)
            # Dosya kilitlenmesini önlemek için kısa bir bekleme
            time.sleep(0.1)
            if os.path.exists(filename):
                os.remove(filename)
        except Exception as e:
            print(f"Konuşma hatası: {e}")

    def listen(self):
        if self.microphone is None:
            print(">>> Mikrofon yok, dinleme yapılamıyor.")
            return None
            
        with self.microphone as source:
            print("\n[Dinleniyor...] Poodle seni duymaya hazır...")
            try:
                # Dinleme sürelerini biraz esnettik
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)
                text = self.recognizer.recognize_google(audio, language=self.lang)
                print(f"Tanem: {text}")
                return text.lower()
            except sr.UnknownValueError:
                print(">>> Poodle: Ne dediğini anlayamadım.")
                return None
            except sr.WaitTimeoutError:
                print(">>> Poodle: Bir şey duymadım.")
                return None
            except Exception as e:
                print(f"Dinleme hatası: {e}")
                return None
