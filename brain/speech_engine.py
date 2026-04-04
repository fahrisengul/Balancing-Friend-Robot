import os
import time
import speech_recognition as sr
from gtts import gTTS
from playsound import playsound

class PoodleSpeech:
    def __init__(self, lang="tr-TR"):
        self.recognizer = sr.Recognizer()
        self.lang = lang
        
        # Mikrofon Hatasını Sönümleme
        try:
            self.microphone = sr.Microphone()
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
            print(">>> [SES] Mikrofon Basarıyla Baglandı.")
        except Exception as e:
            self.microphone = None
            print(f">>> [HATA] Mikrofon bulunamadı veya PyAudio sorunu var: {e}")

    def speak(self, text):
        """Metni sese cevirir ve calar."""
        if not text:
            return
            
        print(f"Poodle: {text}")
        filename = "temp_voice.mp3"
        
        try:
            # Ses dosyasını olustur
            tts = gTTS(text=text, lang="tr")
            tts.save(filename)
            
            # Sesi cal
            playsound(filename)
            
            # Dosyayı temizle (Windows/Mac izin sorunları icin kucuk bir bekleme)
            time.sleep(0.1)
            if os.path.exists(filename):
                os.remove(filename)
        except Exception as e:
            print(f"Konusma Hatası: {e}")

    def listen(self):
        """Mikrofonu dinler ve metne cevirir."""
        if self.microphone is None:
            print(">>> [HATA] Mikrofon erisimi yok, dinleme yapılamıyor.")
            return None

        with self.microphone as source:
            print("\n[Dinleniyor...] Tanem, seni dinliyorum...")
            try:
                # Arka plan gürültüsünü tekrar ayarla
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                # 5 saniye bekle, 5 saniyelik konusma sınırı koy
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=5)
                
                print("[İsleniyor...]")
                text = self.recognizer.recognize_google(audio, language=self.lang)
                print(f"Tanem: {text}")
                return text.lower()
                
            except sr.WaitTimeoutError:
                print("Ses duyulmadı (Zaman asımı).")
                return None
            except sr.UnknownValueError:
                print("Ne dedigini anlayamadım.")
                return None
            except Exception as e:
                print(f"Dinleme Hatası: {e}")
                return None
