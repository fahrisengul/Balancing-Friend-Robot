import os
import wave
import subprocess
import numpy as np
from faster_whisper import WhisperModel
from piper.voice import PiperVoice
import sounddevice as sd # Daha stabil bir ses yakalayıcı

class PoodleSpeech:
    def __init__(self, lang="tr"):
        self.lang = lang
        # 1. Modelleri RAM'e Yükle
        print(">>> Faster-Whisper ve Piper yükleniyor...")
        self.stt = WhisperModel("base", device="cpu", compute_type="int8")
        self.tts = PiperVoice.load("tr_TR-fahrettin-medium.onnx")
        print(">>> [SİSTEM] Poodle hazır! L'ye bas ve konuş, susunca ben anlayacağım.")

    def listen_with_vad(self):
        """Basit ama etkili VAD: Sessizlik olunca durur."""
        print("\n[Dinleniyor...] Konuşman bitince otomatik anlayacağım...")
        fs = 16000
        audio_data = []
        silent_frames = 0
        
        # Sesi dinle (Sounddevice Anaconda ile daha barışıktır)
        with sd.InputStream(samplerate=fs, channels=1, dtype='int16') as stream:
            while True:
                data, overflow = stream.read(512)
                audio_data.append(data)
                
                # Ses seviyesi kontrolü
                rms = np.sqrt(np.mean(data**2))
                if rms < 400: # Sessizlik eşiği
                    silent_frames += 1
                else:
                    silent_frames = 0
                
                # 1.5 saniye sessizlik olursa dur
                if silent_frames > 40 and len(audio_data) > 30: 
                    break
        
        # Dosyaya kaydet ve Whisper'a gönder
        temp_file = "input.wav"
        with wave.open(temp_file, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(fs)
            wf.writeframes(np.concatenate(audio_data).tobytes())
            
        segments, _ = self.stt.transcribe(temp_file, language=self.lang)
        text = "".join(segment.text for segment in segments)
        print(f"Tanem: {text}")
        return text.lower()

    def speak(self, text):
        if not text: return
        print(f"Poodle: {text}")
        filename = "poodle_voice.wav"
        with wave.open(filename, "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(self.tts.config.sample_rate)
            self.tts.synthesize(text, wav_file)
        
        subprocess.run(["afplay", "-q", "1", filename])
        if os.path.exists(filename): os.remove(filename)
