import os
import wave
import array
import queue
import tempfile
import threading
import platform
import subprocess
import time
import re
import unicodedata
from datetime import datetime
from difflib import SequenceMatcher

import numpy as np
import sounddevice as sd
import torch

from faster_whisper import WhisperModel
from piper.voice import PiperVoice
from silero_vad import load_silero_vad, get_speech_timestamps

def get_now():
    """Milisaniye hassasiyetinde zaman damgası üretir."""
    return datetime.now().strftime("%H:%M:%S.%f")[:-3]

def log_time(message):
    print(f"[{get_now()}] {message}")

class PoodleSpeech:
    def __init__(
        self,
        lang="tr",
        input_samplerate=16000,
        whisper_model_size="base",
        whisper_compute_type="int8",
        input_device=None,
    ):
        self.lang = lang
        self.input_samplerate = input_samplerate
        self.block_duration_ms = 200
        self.block_size = int(self.input_samplerate * self.block_duration_ms / 1000)

        self.audio_queue = queue.Queue()
        self.event_queue = queue.Queue()

        self._listener_running = False
        self._busy = False
        self._muted = False
        
        log_time(">>> Whisper modeli yükleniyor...")
        self.stt_model = WhisperModel(whisper_model_size, device="cpu", compute_type=whisper_compute_type)
        
        log_time(">>> Silero VAD yükleniyor...")
        self.vad_model = load_silero_vad()
        
        log_time(">>> Piper modeli yükleniyor...")
        # Model dosya adının klasöründekiyle aynı olduğundan emin ol
        self.voice = PiperVoice.load("tr_TR-fahrettin-medium.onnx")
        
        self.input_device = input_device
        log_time(">>> [SES] Doğal dinleme + STT + Piper TTS hazır.")

    def debug_list_input_devices(self):
        devices = sd.query_devices()
        log_time(">>> [MIC DEBUG] Erişilebilir giriş cihazları:")
        for i, d in enumerate(devices):
            if d['max_input_channels'] > 0:
                print(f"    #{i}: {d['name']} | in={d['max_input_channels']}")

    def is_muted(self): return self._muted
    def set_busy(self, val): self._busy = val

    def start_auto_listener(self):
        self._listener_running = True
        threading.Thread(target=self._listener_loop, daemon=True).start()
        log_time("[DINLEME MODU] Arka planda dinleme başladı...")

    def stop_auto_listener(self):
        self._listener_running = False

    def get_pending_event(self):
        try:
            return self.event_queue.get_now_callback() if hasattr(self.event_queue, 'get_now_callback') else self.event_queue.get_nowait()
        except:
            return {"type": "none"}

    def _listener_loop(self):
        stream = sd.InputStream(
            samplerate=self.input_samplerate,
            channels=1,
            blocksize=self.block_size,
            device=self.input_device,
            callback=lambda d, f, t, s: self.audio_queue.put(d.copy())
        )
        
        with stream:
            collected_audio = []
            silent_blocks = 0
            recording = False

            while self._listener_running:
                try:
                    block = self.audio_queue.get(timeout=1)
                except queue.Empty:
                    continue

                if self._busy:
                    collected_audio = []
                    recording = False
                    continue

                audio_float32 = block.flatten()
                peak = np.max(np.abs(audio_float32))
                rms = np.sqrt(np.mean(audio_float32**2))

                # VAD Kontrolü
                speech_ts = get_speech_timestamps(
                    torch.from_numpy(audio_float32), 
                    self.vad_model, 
                    sampling_rate=self.input_samplerate
                )

                if len(speech_ts) > 0:
                    if not recording:
                        log_time(f">>> [AUDIO] Ses algılandı (Peak: {peak:.4f})")
                        recording = True
                    collected_audio.append(audio_float32)
                    silent_blocks = 0
                elif recording:
                    collected_audio.append(audio_float32)
                    silent_blocks += 1
                    
                    # 1 saniye sessizlik olursa konuşma bitti say (5 x 200ms)
                    if silent_blocks > 5:
                        full_audio = np.concatenate(collected_audio)
                        log_time(">>> [VAD] Konuşma bitti, transkript ediliyor...")
                        self._process_speech(full_audio)
                        collected_audio = []
                        recording = False
                        silent_blocks = 0

    def _process_speech(self, audio_data):
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp_path = tmp.name
        
        # Sesi kaydet
        with wave.open(tmp_path, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(self.input_samplerate)
            wf.writeframes((audio_data * 32767).astype(np.int16).tobytes())

        # Whisper Transkript
        segments, _ = self.stt_model.transcribe(tmp_path, language=self.lang)
        text = " ".join([s.text for s in segments]).strip()
        os.remove(tmp_path)

        if not text: return

        log_time(f">>> [STT DEBUG] transcript: {text}")

        # Sus/Sessiz ol kontrolü
        if any(w in text.lower() for w in ["sus", "sessiz ol", "dur"]):
            self._muted = True
            log_time(">>> [MODE] Robot sessiz moda geçti.")
            self.event_queue.put({"type": "sleep"})
            return

        # Hey/Uyan kontrolü
        if self._muted:
            if "hey" in text.lower() or SequenceMatcher(None, text.lower(), "hey").ratio() > 0.7:
                self._muted = False
                log_time(">>> [MODE] Robot tekrar aktif.")
                self.event_queue.put({"type": "resumed"})
            return

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
                # Piper RAM'deki modelden sesi doğrudan yazar
                self.voice.synthesize(text, wav_file)

            # Mac/Linux çalma komutu
            play_cmd = "afplay" if platform.system() == "Darwin" else "aplay"
            subprocess.run([play_cmd, "-q", "1", temp_path])
            
            if os.path.exists(temp_path):
                os.remove(temp_path)
                
        except Exception as e:
            log_time(f">>> [TTS HATASI] {e}")
        finally:
            self._busy = False
