import os
import subprocess
import time
import speech_recognition as sr

class PoodleSpeech:
    def __init__(self, lang="tr-TR"):
        self.recognizer = sr.Recognizer()
        self.lang = lang
        self.model_path = "tr_TR-dfki-medium.onnx" 
        self.piper_path = "./piper" 
        
        # Mikrofon Hassasiyet Ayarları
        self.recognizer.energy_threshold = 400
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 0.8
        
        try:
            import pyaudio
            self.microphone = sr.Microphone()
            print(">>> [SES] Mikrofon ve Piper TTS Tam Kapasite Hazır.")
        except Exception as e:
            self.microphone = None
            print(f">>> [UYARI] Mikrofon donanımı eksik: {e}")

    def speak(self, text):
        """Piper ile milisaniyeler içinde ses üretir."""
        if not text: return
        print(f"Poodle: {text}")
        
        try:
            filename = "poodle_voice.wav"
            # Mac için Piper komut yapısı
            command = f'echo "{text}" | {self.piper_path} --model {self.model_path} --output_file {filename}'
            subprocess.run(command, shell=True, check=True)
            
            # Sesi çal (Mac için afplay)
            if os.path.exists(filename):
                subprocess.run(["afplay", filename])
                os.remove(filename)
        except Exception as e:
            print(f">>> [HATA] Piper Ses Üretimi Başarısız: {e}")

    def listen(self):
        """Tanem'in sesini duyan kulaklar."""
        if self.microphone is None:
            return None
            
        with self.microphone as source:
            print("\n[Dinleniyor...] Poodle seni duyabilir...")
            try:
                # Gürültü kalibrasyonunu kısa tutalım
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)
                text = self.recognizer.recognize_google(audio, language=self.lang)
                print(f"Tanem: {text}")
                return text.lower()
            except sr.UnknownValueError:
                return None
            except Exception as e:
                print(f">>> [HATA] Dinleme sorunu: {e}")
                return None
