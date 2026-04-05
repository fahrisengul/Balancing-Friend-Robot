import os
import subprocess
import time
import speech_recognition as sr

class PoodleSpeech:
    def __init__(self, lang="tr-TR"):
        self.recognizer = sr.Recognizer()
        self.lang = lang
        self.model_path = "tr_TR-dfki-medium.onnx"
        
        self.recognizer.energy_threshold = 400
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 0.8
        
        try:
            import pyaudio
            self.microphone = sr.Microphone()
            print(">>> [SES] Mikrofon ve Piper (Python) Hazır.")
        except Exception as e:
            self.microphone = None
            print(f">>> [UYARI] Mikrofon hatası: {e}")

    def speak(self, text):
        if not text: return
        print(f"Poodle: {text}")
        
        try:
            import wave
            import subprocess
            from piper.voice import PiperVoice
            
            filename = "poodle_voice.wav"
            
            # Piper Ses Modelini Yükle
            voice = PiperVoice.load(self.model_path)
            
            # --- EN BASİT VE OTOMATİK DOSYA YAZMA YÖNTEMİ ---
            # wave.open yerine direkt open(filename, 'wb') kullanıyoruz
            # Piper kütüphanesi wave header'larını kendi ekler
            with open(filename, "wb") as wav_file:
                voice.synthesize(text, wav_file)
            
            # SESİ ÇAL (afplay yerleşik Mac aracıdır)
            if os.path.exists(filename):
                subprocess.run(["afplay", filename])
                os.remove(filename)
                
        except Exception as e:
            print(f">>> [SES KRİZİ] Piper sentez hatası: {e}")

    def listen(self):
        if self.microphone is None:
            return None
            
        with self.microphone as source:
            print("\n[Dinleniyor...] Poodle seni duymaya hazır...")
            try:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)
                text = self.recognizer.recognize_google(audio, language=self.lang)
                print(f"Tanem: {text}")
                return text.lower()
            except:
                return None
