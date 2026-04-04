import os
import time
import speech_recognition as sr
from gtts import gTTS
from playsound import playsound

class PoodleSpeech:
    def __init__(self, lang="tr-TR"):
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.lang = lang
        
    def speak(self, text):
        """Metni sese çevirir ve çalar."""
        if not text: return
        
        print(f"Poodle diyor ki: {text}")
        try:
            tts = gTTS(text=text, lang="tr")
            filename = "temp_voice.mp3"
            tts.save(filename)
            playsound(filename)
            os.remove(filename) # Çaldıktan sonra dosyayı temizle
        except Exception as e:
            print(f"Konuşma hatası: {e}")

    def listen(self):
        """Mikrofonu dinler ve söylenenleri metne çevirir."""
        with self.microphone as source:
            print("\n[Dinleniyor...] Tanem bir şey söyleyebilirsin.")
            self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
            try:
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=5)
                print("[İşleniyor...]")
                text = self.recognizer.recognize_google(audio, language=self.lang)
                print(f"Tanem: {text}")
                return text.lower()
            except sr.WaitTimeoutError:
                print("Ses duyulmadı.")
                return None
            except sr.UnknownValueError:
                print("Anlaşılamadı.")
                return None
            except Exception as e:
                print(f"Dinleme hatası: {e}")
                return None
