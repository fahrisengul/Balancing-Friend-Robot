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
        
        # PyAudio kontrolünü en başta yapıyoruz ki sr.Microphone() patlatmasın
        try:
            import pyaudio
            self.microphone = sr.Microphone()
            print(">>> [SES] Mikrofon başarıyla bağlandı.")
        except (ImportError, AttributeError, Exception) as e:
            print(f">>> [UYARI] PyAudio veya Mikrofon sorunu: {e}")
            print(">>> Sesli komutlar devre dışı ama Poodle görseli çalışacak.")

    def speak(self, text):
        if not text: return
        print(f"Poodle: {text}")
        try:
            tts = gTTS(text=text, lang="tr")
            filename = "temp_voice.mp3"
            tts.save(filename)
            playsound(filename)
            if os.path.exists(filename):
                os.remove(filename)
        except Exception as e:
            print(f"Konuşma hatası: {e}")

    def listen(self):
        if self.microphone is None:
            print(">>> Mikrofon başlatılamadığı için dinleme yapılamıyor.")
            return None
            
        with self.microphone as source:
            print("\n[Dinleniyor...] Tanem, seni dinliyorum...")
            self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
            try:
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=5)
                text = self.recognizer.recognize_google(audio, language=self.lang)
                print(f"Tanem: {text}")
                return text.lower()
            except Exception:
                return None
