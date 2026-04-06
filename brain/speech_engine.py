import os
import wave
import tempfile
import threading
import platform
import subprocess
import time
from datetime import datetime
from pvrecorder import PvRecorder 
import numpy as np
import torch
from faster_whisper import WhisperModel
from piper.voice import PiperVoice
from silero_vad import load_silero_vad, get_speech_timestamps

def get_now():
    return datetime.now().strftime("%H:%M:%S.%f")[:-3]

def log_time(message):
    print(f"[{get_now()}] {message}")

class PoodleSpeech:
    def __init__(self, lang="tr", input_device_index=-1):
        self.lang = lang
        self.frame_length = 512 
        self.event_queue = [] 

        self._listener_running = False
        self._busy = False
        self._muted = False
        self.recorder = None
        
        log_time(">>> Modeller yükleniyor (Whisper/VAD/Piper)...")
        self.stt_model = WhisperModel("base", device="cpu", compute_type="int8")
        self.vad_model = load_silero_vad()
        self.voice = PiperVoice.load("tr_TR-fahrettin-medium.onnx")
        
        self.device_index = input_device_index
        log_time(">>> [SES] Tüm sistemler hazır.")

    def debug_list_input_devices(self):
        devices = PvRecorder.get_available_devices()
        log_time(">>> [MIC DEBUG] Cihaz Listesi:")
        for i, name in enumerate(devices):
            print(f"    #{i}: {name}")

    def is_muted(self): return self._muted
    def set_busy(self, val): self._busy = val

    def start_auto_listener(self):
        if self._listener_running: return
        self._listener_running = True
        threading.Thread(target=self._listener_loop, daemon=True).start()
        log_time("[DINLEME MODU] Arka plan dinlemesi aktif.")

    def stop_auto_listener(self):
        self._listener_running = False
        if self.recorder:
            self.recorder.stop()

    def get_pending_event(self):
        if len(self.event_queue) > 0:
            return self.event_queue.pop(0)
        return {"type": "none"}

    def _listener_loop(self):
        self.recorder = PvRecorder(device_index=self.device_index, frame_length=self.frame_length)
        self.recorder.start()
        
        collected_audio = []
        silent_frames = 0
        recording = False

        try:
            while self._listener_running:
                frame = self.recorder.read()
                
                if self._busy:
                    collected_audio = []
                    recording = False
                    continue

                audio_float32 = np.array(frame, dtype=np.float32) / 32768.0
                audio_tensor = torch.from_numpy(audio_float32)
                
                speech_ts = get_speech_timestamps(audio_tensor, self.vad_model, sampling_rate=16000)

                if len(speech_ts) > 0:
                    if not recording:
                        log_time(">>> [AUDIO] Ses algılandı...")
                        recording = True
                    collected_audio.extend(frame)
                    silent_frames = 0
                elif recording:
                    collected_audio.extend(frame)
                    silent_frames += 1
                    
                    if silent_frames > 40: # Yaklaşık 1.2 saniye sessizlik
                        log_time(">>> [VAD] Konuşma bitti, işleniyor...")
                        self._process_speech(np.array(collected_audio, dtype=np.int16))
                        collected_audio = []
                        recording = False
                        silent_frames = 0
        except Exception as e:
            log_time(f">>> [RECORDER ERROR] {e}")
        finally:
            if self.recorder:
                self.recorder.stop()
                self.recorder.delete()

    def _process_speech(self, audio_int16):
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp_path = tmp.name
        
        with wave.open(tmp_path, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(16000)
            wf.writeframes(audio_int16.tobytes())

        segments, _ = self.stt_model.transcribe(tmp_path, language=self.lang)
        text = " ".join([s.text for s in segments]).strip()
        
        try: os.remove(tmp_path)
        except: pass

        if not text or len(text) < 2: return
        log_time(f">>> [STT] '{text}'")

        if any(w in text.lower() for w in ["sus", "sessiz ol", "dur"]):
            self._muted = True
            log_time(">>> [MODE] Sessiz mod.")
            self.event_queue.append({"type": "sleep"})
            return

        if self._muted and ("hey" in text.lower()):
            self._muted = False
            log_time(">>> [MODE] Aktif mod.")
            self.event_queue.append({"type": "resumed"})
            return

        if not self._muted:
            self.event_queue.append({"type": "command", "text": text})

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
            subprocess.run([cmd, temp_path])
            
            try: os.remove(temp_path)
            except: pass
        finally:
            self._busy = False
