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
            import wave
            # 1. DOSYAYI AÇIYORUZ VE TÜM TEKNİK DETAYLARI ELLE ZORLUYORUZ
            with wave.open(filename, "wb") as wav_file:
                # Piper modelleri (Fahrettin/DFKI) genelde 1 kanal (Mono) ve 16-bit'tir
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2) # 16-bit
                wav_file.setframerate(self.voice.config.sample_rate)
                
                # 2. SESİ ŞİMDİ SENTEZLE (Artık wave hata veremez, her şeyi söyledik)
                self.voice.synthesize(text, wav_file)
            
            # 3. SESİ ÇAL
            if os.path.exists(filename):
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
