import os
import wave
import queue
import tempfile
import threading
import platform
import subprocess
import time
from datetime import datetime
from difflib import SequenceMatcher

import numpy as np
import sounddevice as sd
import torch

from faster_whisper import WhisperModel
from piper.voice import PiperVoice
from silero_vad import load_silero_vad, get_speech_timestamps

def get_now():
    """HH:MM:SS.ms formatında zaman döner."""
    return datetime.now().strftime("%H:%M:%S.%f")[:-3]

def log_time(message):
    print(f"[{get_now()}] {message}")

class PoodleSpeech:
    def __init__(self, lang="tr", input_device=None):
        self.lang = lang
        self.input_samplerate = 16000
        self.block_size = 3200  # 200ms bloklar
        
        self.audio_queue = queue.Queue()
        self.event_queue = queue.Queue()

        self._listener_running = False
        self._busy = False
        self._muted = False
        
        log_time(">>> Modeller yükleniyor (Whisper/VAD/Piper)...")
        self.stt_model = WhisperModel("base", device="cpu", compute_type="int8")
        self.vad_model = load_silero_vad()
        self.voice = PiperVoice.load("tr_TR-fahrettin-medium.onnx")
        
        self.input_device = input_device
        log_time(">>> [SES] Tüm sistemler hazır.")

    def debug_list_input_devices(self):
        devices = sd.query_devices()
        log_time(">>> [MIC DEBUG] Cihaz Listesi:")
        for i, d in enumerate(devices):
            if d['max_input_channels'] > 0:
                print(f"    #{i}: {d['name']}")

    def is_muted(self): return self._muted
    def set_busy(self, val): self._busy = val

    def start_auto_listener(self):
        self._listener_running = True
        threading.Thread(target=self._listener_loop, daemon=True).start()
        log_time("[DINLEME MODU] Arka plan dinlemesi aktif.")

    def stop_auto_listener(self):
        self._listener_running = False

    def get_pending_event(self):
        try:
            return self.event_queue.get_nowait()
        except:
            return {"type": "none"}

    def _listener_loop(self):
        # M serisi Mac'ler için en stabil buffer ayarı
        def audio_callback(indata, frames, time_info, status):
            if status:
                print(status)
            self.audio_queue.put(indata.copy())

        try:
            with sd.InputStream(samplerate=self.input_samplerate, channels=1, 
                                device=self.input_device, callback=audio_callback):
                collected_audio = []
                silent_blocks = 0
                recording = False

                while self._listener_running:
                    block = self.audio_queue.get()
                    if self._busy:
                        collected_audio = []
                        recording = False
                        continue

                    # VAD işlemesi (Float32 tensör ile)
                    audio_tensor = torch.from_numpy(block.flatten().astype(np.float32))
                    speech_ts = get_speech_timestamps(audio_tensor, self.vad_model, sampling_rate=16000)

                    if len(speech_ts) > 0:
                        if not recording:
                            log_time(">>> [AUDIO] Ses başladı...")
                            recording = True
                        collected_audio.append(block.flatten())
                        silent_blocks = 0
                    elif recording:
                        collected_audio.append(block.flatten())
                        silent_blocks += 1
                        
                        # 1 saniye sessizlik (5 blok x 200ms)
                        if silent_blocks > 5:
                            log_time(">>> [VAD] Konuşma bitti, işleniyor...")
                            full_audio = np.concatenate(collected_audio)
                            self._process_speech(full_audio)
                            collected_audio = []
                            recording = False
                            silent_blocks = 0
        except Exception as e:
            log_time(f">>> [MIC HATASI] {e}")

    def _process_speech(self, audio_data):
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp_path = tmp.name
        
        with wave.open(tmp_path, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(16000)
            wf.writeframes((audio_data * 32767).astype(np.int16).tobytes())

        segments, _ = self.stt_model.transcribe(tmp_path, language=self.lang)
        text = " ".join([s.text for s in segments]).strip()
        os.remove(tmp_path)

        if not text: return
        log_time(f">>> [STT] Metin: {text}")

        if any(w in text.lower() for w in ["sus", "sessiz ol", "dur"]):
            self._muted = True
            log_time(">>> [MODE] Sessiz mod.")
            self.event_queue.put({"type": "sleep"})
            return

        if self._muted and ("hey" in text.lower()):
            self._muted = False
            log_time(">>> [MODE] Aktif mod.")
            self.event_queue.put({"type": "resumed"})
            return

        if not self._muted:
            self.event_queue.put({"type": "command", "text": text})

    def speak(self, text):
        if not text: return
        log_time(f"Poodle: {text}")
        self._busy = True
        
        try:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                temp_path = tmp.name

            with wave.open(temp_path, "wb") as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(self.voice.config.sample_rate)
                self.voice.synthesize(text, wav_file)

            cmd = "afplay" if platform.system() == "Darwin" else "aplay"
            subprocess.run([cmd, "-q", "1", temp_path])
            if os.path.exists(temp_path): os.remove(temp_path)
        finally:
            self._busy = False
