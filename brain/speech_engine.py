import os
import subprocess
import time
import speech_recognition as sr

class PoodleSpeech:
    def __init__(self, lang="tr-TR"):
        self.recognizer = sr.Recognizer()
        self.lang = lang
        # Dosyaların tam yolunu kontrol et (Aynı klasörde olduklarını varsayıyorum)
        self.model_path = "tr_TR-dfki-medium.onnx" 
        self.piper_path = "./piper" # İndirdiğin piper binary dosyası
        
        # Mikrofon Ayarları
        self.recognizer.energy_threshold = 300
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 0.8
        
        try:
            import pyaudio
            self.microphone = sr.Microphone()
            print(">>> [SES] Mikrofon ve Piper TTS Tam Kapasite Hazır.")
        except Exception as e:
            self.microphone = None
            print(f">>> [HATA] Donanım sorunu: {e}")

    def speak(self, text):
        if not text: return
        print(f"Poodle: {text}")
        
        try:
            filename = "poodle_voice.wav"
            
            # Piper komutu (Yerel binary üzerinden çalışır)
            # Not: Mac'te 'echo' ve 'piper' arasında bir köprü kuruyoruz
            command = f'echo "{text}" | {self.piper_path} --model {self.model_path} --output_file {filename}'
            subprocess.run(command, shell=True, check=True)
            
            # Sesi çal (Mac için afplay)
            subprocess.run(["afplay", filename])
            
            if os.path.exists(filename):
                os.remove(filename)
        except Exception as e:
            print(f"Piper TTS Hatası: {e}. (Dosya izinlerini ve piper yolunu kontrol et)")

    def listen(self):
        if self.microphone is None:
            return None
            
        with self.microphone as source:
            print("\n[Dinleniyor...] Poodle seni duymaya hazır...")
            try:
                # Gürültü kalibrasyonunu her seferinde kısa tutuyoruz
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)
                text = self.recognizer.recognize_google(audio, language=self.lang)
                print(f"Tanem: {text}")
                return text.lower()
            except Exception:
                return None
