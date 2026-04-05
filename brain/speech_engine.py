import os
import subprocess
import time
import speech_recognition as sr

class PoodleSpeech:
    def __init__(self, lang="tr-TR"):
        self.recognizer = sr.Recognizer()
        self.lang = lang
        # Elimizdeki mevcut model:
        self.model_path = "tr_TR-fahrettin-medium.onnx"
        
        try:
            import pyaudio
            self.microphone = sr.Microphone()
            print(">>> [SES] Mikrofon ve DFKI Ses Motoru Optimize Edildi.")
        except Exception as e:
            print(f">>> [HATA] Mikrofon sorunu: {e}")

    # speech_engine.py - speak fonksiyonu hız ayarı
    def speak(self, text):
        if not text: return
        print(f"Poodle: {text}")
        
        filename = "poodle_voice.wav"
        try:
            clean_text = ''.join(e for e in text if e.isalnum() or e.isspace() or e in ".,?!")
            # GECİKMEYİ AZALTMAK İÇİN: 
            # Modeli her seferinde değil, bir kez yükleyip RAM'de tutmak en iyisidir 
            # ama şu anki yapı için komutu en yalın haliyle gönderiyoruz:
            command = f'echo "{clean_text}" | python -m piper --model {self.model_path} --output_file {filename}'
            
            # subprocess.call, run'dan daha hızlı tetiklenir bazen
            subprocess.call(command, shell=True)
            
            if os.path.exists(filename):
                # afplay -v (volume) ve -q 1 ile en hızlı tetikleme
                subprocess.run(["afplay", "-q", "1", filename])
                os.remove(filename)
        except Exception as e:
            print(f">>> [HATA] {e}")

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
