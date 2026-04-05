import os
import wave
import struct
import numpy as np
import subprocess
from openwakeword.model_storage import download_models
from faster_whisper import WhisperModel
from piper.voice import PiperVoice
from pvrecorder import PvRecorder

class PoodleEngine:
    def __init__(self):
        # 1. Modelleri Yükle (RAM'de sıcak tut)
        print(">>> Poodle beyin hücreleri yükleniyor...")
        self.stt = WhisperModel("base", device="cpu", compute_type="int8")
        self.tts = PiperVoice.load("tr_TR-fahrettin-medium.onnx")
        
        # Wake Word Modeli (Eğer 'Hey Poodle' yoksa yakındaki bir kelimeye eğitiriz)
        download_models() # Standart modelleri indirir
        
        # Ses Ayarları
        self.recorder = PvRecorder(device_index=-1, frame_length=512)
        print(">>> [SİSTEM] Hey Poodle! demeni bekliyorum...")

    def listen_for_wake_word(self):
        """'Hey Poodle' denene kadar sessizce bekler (Prior 1)"""
        self.recorder.start()
        try:
            while True:
                frame = self.recorder.read()
                # Burada Wake Word algılama mantığı çalışacak (openwakeword)
                # Şimdilik simüle ediyoruz, 'Hey Poodle' algılandı varsayalım:
                if self._detect_wake_word(frame):
                    print(">>> [UYANDI] Efendim Tanem?")
                    return True
        finally:
            self.recorder.stop()

    def capture_with_vad(self):
        """Tanem sustuğunda kaydı otomatik durdurur (Prior 2)"""
        print("[Dinliyor...] Konuşman bitince otomatik anlayacağım.")
        audio_data = []
        silent_frames = 0
        max_silent_frames = 30 # Yaklaşık 1-1.5 saniye sessizlik
        
        self.recorder.start()
        while True:
            frame = self.recorder.read()
            audio_data.extend(frame)
            
            # Ses şiddeti kontrolü (Basit VAD)
            rms = np.sqrt(np.mean(np.array(frame)**2))
            if rms < 500: # Sessizlik eşiği
                silent_frames += 1
            else:
                silent_frames = 0
            
            # Tanem sustuysa döngüden çık
            if silent_frames > max_silent_frames and len(audio_data) > 16000:
                break
        
        self.recorder.stop()
        return np.array(audio_data, dtype=np.int16)

    def speak(self, text):
        """Gecikmesiz ve hatasız ses üretimi."""
        filename = "poodle_voice.wav"
        with wave.open(filename, "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(self.tts.config.sample_rate)
            self.tts.synthesize(text, wav_file)
        
        # Mac'te afplay, Pi'de aplay
        play_cmd = "afplay" if os.uname().sysname == 'Darwin' else "aplay"
        subprocess.run([play_cmd, "-q", filename])
        if os.path.exists(filename): os.remove(filename)

    def _detect_wake_word(self, frame):
        # Gerçek implementasyonda openwakeword buraya bağlanacak
        # Şimdilik bir tuşa basılmış gibi veya yüksek sesle tetiklenebilir
        return True
