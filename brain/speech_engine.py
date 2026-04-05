import os
import subprocess
import time
import speech_recognition as sr

class PoodleSpeech:
    def __init__(self, lang="tr-TR"):
        self.recognizer = sr.Recognizer()
        self.lang = lang
        # Elimizdeki mevcut model:
        self.model_path = "tr_TR-dfki-medium.onnx"
        
        try:
            import pyaudio
            self.microphone = sr.Microphone()
            print(">>> [SES] Mikrofon ve DFKI Ses Motoru Optimize Edildi.")
        except Exception as e:
            print(f">>> [HATA] Mikrofon sorunu: {e}")

    def speak(self, text):
        if not text: return
        # Terminalde temiz görünmesi için kısa keselim
        print(f"Poodle: {text}")
        
        filename = "poodle_voice.wav"
        
        try:
            # 1. METNİ TEMİZLE (Karakter hatalarını önler)
            clean_text = text.replace('"', '').replace("'", "").replace("\n", " ")
            
            # 2. EN HIZLI ÜRETİM (Terminal Pipeline)
            # 'python' komutu senin Anaconda (base) ortamını kullanır
            command = f'echo "{clean_text}" | python -m piper --model {self.model_path} --output_file {filename}'
            
            # Sesi üret (Arka planda sessizce ve hızlıca)
            subprocess.run(command, shell=True, check=True, capture_output=True)
            
            # 3. ANLIK ÇALMA
            if os.path.exists(filename):
                # 'afplay' Mac'in en hızlı ses çalarıdır
                subprocess.run(["afplay", filename])
                os.remove(filename)
                
        except Exception as e:
            print(f">>> [SES HATASI] Üretim sırasında bir sorun oluştu: {e}")

    def listen(self):
        """Hızlı dinleme modülü."""
        if not self.microphone: return None
        with self.microphone as source:
            print("\n[Dinleniyor...] Poodle seni duymaya hazır...")
            try:
                # Kalibrasyonu 0.3 saniyeye düşürerek tepki hızını artırdık
                self.recognizer.adjust_for_ambient_noise(source, duration=0.3)
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=8)
                text = self.recognizer.recognize_google(audio, language=self.lang)
                print(f"Tanem: {text}")
                return text.lower()
            except:
                return None
