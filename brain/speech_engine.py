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
            import subprocess
            from piper.voice import PiperVoice
            
            filename = "poodle_voice.wav"
            
            # Piper Ses Modelini Yükle
            voice = PiperVoice.load(self.model_path)
            
            # --- WAVE KÜTÜPHANESİNİ DEVRE DIŞI BIRAKAN YÖNTEM ---
            # Sesi bir liste (iterator) olarak üretiyoruz
            with open(filename, "wb") as wav_file:
                # synthesize_ids_to_audio yerine doğrudan synthesize kullanıyoruz
                # ama wave_file nesnesini değil, ham binary yazma yöntemini seçiyoruz
                for audio_bytes in voice.synthesize_stream(text):
                    wav_file.write(audio_bytes)
            
            # SESİ ÇAL
            if os.path.exists(filename):
                # afplay bazen 'raw' dosyaları sevmez, o yüzden en garantisi subprocess
                subprocess.run(["afplay", filename])
                os.remove(filename)
                
        except Exception as e:
            # EĞER YUKARIDAKİ DE HATA VERİRSE (SON ÇARE - TERMINAL YÖNTEMİ AMA ABSOLUTE PATH İLE)
            try:
                python_path = "/Users/fahrisengul/anaconda3/bin/python"
                clean_text = text.replace('"', '').replace("'", "")
                cmd = f'echo "{clean_text}" | {python_path} -m piper --model {self.model_path} --output_file {filename}'
                subprocess.run(cmd, shell=True, check=True)
                subprocess.run(["afplay", filename])
                if os.path.exists(filename): os.remove(filename)
            except Exception as e2:
                print(f">>> [SES KRİZİ] Piper sentez hatası: {e2}")

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
