import os
import subprocess
import time
import speech_recognition as sr

class PoodleSpeech:
    def __init__(self, lang="tr-TR"):
        self.recognizer = sr.Recognizer()
        self.lang = lang
        self.model_path = "tr_TR-dfki-medium.onnx" # İndirdiğin dosya yolu
        
        try:
            import pyaudio
            self.microphone = sr.Microphone()
            print(">>> [SES] Mikrofon ve Piper TTS Hazır.")
        except:
            print(">>> [HATA] Mikrofon donanımı eksik.")

    def speak(self, text):
        if not text: return
        print(f"Poodle: {text}")
        
        # Piper ile OFFLINE ve HIZLI ses üretimi
        # 'aplay' yerine Mac'te 'afplay' kullanılır
        try:
            start_time = time.time()
            filename = "poodle_voice.wav"
            
            # Piper komutu: Metni al, ses dosyasına çevir
            command = f'echo "{text}" | piper --model {self.model_path} --output_file {filename}'
            subprocess.run(command, shell=True, check=True)
            
            # Sesi çal (Mac için afplay)
            subprocess.run(["afplay", filename])
            
            print(f">>> [HIZ] Ses üretim süresi: {time.time() - start_time:.2f} sn")
            
            if os.path.exists(filename):
                os.remove(filename)
        except Exception as e:
            print(f"Piper Hatası: {e}")

    # listen() fonksiyonun aynı kalabilir...
