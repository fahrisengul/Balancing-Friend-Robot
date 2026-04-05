import os
import wave
import subprocess
import speech_recognition as sr
from piper.voice import PiperVoice  # Modeli RAM'e almak için şart

class PoodleSpeech:
    def __init__(self, lang="tr-TR"):
        self.recognizer = sr.Recognizer()
        self.lang = lang
        # Model adını klasöründekiyle eşleştir (Fahrettin veya DFKI)
        self.model_path = "tr_TR-fahrettin-medium.onnx" 
        
        try:
            # --- KRİTİK: Modeli RAM'e yüklüyoruz (Gecikmeyi bitiren kısım) ---
            print(">>> Piper modeli belleğe yükleniyor (Lütfen bekleyin)...")
            self.voice = PiperVoice.load(self.model_path)
            
            import pyaudio
            self.microphone = sr.Microphone()
            print(">>> [SES] Poodle kulağını açtı, ses motoru sıcak ve hazır!")
        except Exception as e:
            print(f">>> [HATA] Başlatma hatası: {e}")

    def speak(self, text):
        if not text: return
        print(f"Poodle: {text}")
        
        filename = "poodle_voice.wav"
        try:
            # 1. Sesi RAM'deki modelle milisaniyeler içinde üret
            with wave.open(filename, "wb") as wav_file:
                # Piper'ın iç ayarlarını otomatik kullanıyoruz
                self.voice.synthesize(text, wav_file)
            
            # 2. Üretilen dosyayı anında çal
            if os.path.exists(filename):
                # '-q 1' parametresi afplay'in en hızlı başlama modudur
                subprocess.run(["afplay", "-q", "1", filename])
                os.remove(filename)
        except Exception as e:
            print(f">>> [SES HATASI] {e}")

    def listen(self):
        if not self.microphone: return None
        with self.microphone as source:
            print("\n[Dinleniyor...] Poodle seni duymaya hazır...")
            try:
                # Tanem konuşmaya başladığı an yakalaması için hassas ayar
                self.recognizer.adjust_for_ambient_noise(source, duration=0.2)
                audio = self.recognizer.listen(source, timeout=4, phrase_time_limit=6)
                text = self.recognizer.recognize_google(audio, language=self.lang)
                print(f"Tanem: {text}")
                return text.lower()
            except: return None
