import os
import wave
import tempfile
import threading
import platform
import subprocess
import time
import queue
from datetime import datetime
from collections import deque
import array
import re

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
        self.sample_rate = 16000
        self.frame_length = 512

        self.event_queue = queue.Queue()
        self.stt_queue = queue.Queue(maxsize=2)

        self._listener_running = False
        self._busy = False
        self._muted = False
        self._last_tts_time = 0.0
        self._tts_cooldown_sec = 2.2
        self._shutting_down = False

        self.recorder = None
        self.audio_lock = threading.Lock()
        
        # UI/Görsel Seviyeler
        self._input_level = 0.0
        self._tts_level = 0.0
        self._tts_peak_level = 0.0
        self._tts_play_until = 0.0

        log_time(">>> Modeller yükleniyor (Whisper/VAD/Piper)...")
        # Mac için 'small' veya 'base' performansı idealdir
        self.stt_model = WhisperModel("small", device="cpu", compute_type="int8")
        self.vad_model = load_silero_vad()
        self.voice = PiperVoice.load("tr_TR-fahrettin-medium.onnx")
        
        self.device_index = input_device_index
        log_time(">>> [SES] Tüm sistemler hazır.")

    def debug_list_input_devices(self):
        devices = PvRecorder.get_available_devices()
        log_time(">>> [MIC DEBUG] Cihaz Listesi:")
        for i, name in enumerate(devices):
            print(f"    #{i}: {name}")

    def start_auto_listener(self):
        if self._listener_running: return
        self._listener_running = True
        self.listener_thread = threading.Thread(target=self._listener_loop, daemon=True)
        self.stt_worker_thread = threading.Thread(target=self._stt_worker_loop, daemon=True)
        self.listener_thread.start()
        self.stt_worker_thread.start()

    def stop_auto_listener(self):
        self._listener_running = False
        self._shutting_down = True
        if self.recorder:
            try: self.recorder.stop()
            except: pass

    def get_pending_event(self):
        try:
            return self.event_queue.get_nowait()
        except queue.Empty:
            return {"type": "none"}

    def _has_speech(self, audio_float32, threshold=0.30):
        if len(audio_float32) == 0: return False
        audio_tensor = torch.from_numpy(audio_float32)
        speech_ts = get_speech_timestamps(
            audio_tensor, self.vad_model, 
            sampling_rate=self.sample_rate, 
            threshold=threshold
        )
        return len(speech_ts) > 0

    def _listener_loop(self):
        self.recorder = PvRecorder(device_index=self.device_index, frame_length=self.frame_length)
        self.recorder.start()
        
        pre_roll = deque(maxlen=15)
        analysis_window = deque(maxlen=10)
        collected_audio = []
        silent_frames = 0
        recording = False

        try:
            while self._listener_running:
                frame = self.recorder.read()
                if self._busy or self._shutting_down:
                    pre_roll.clear(); analysis_window.clear(); collected_audio = []
                    recording = False; continue

                frame_np = np.array(frame, dtype=np.int16)
                frame_f32 = frame_np.astype(np.float32) / 32768.0

                # UI Input Seviyesi
                rms = float(np.sqrt(np.mean(np.square(frame_f32)))) if len(frame_f32) else 0.0
                norm_rms = min(1.0, rms * 18.0)
                self._input_level += (norm_rms - self._input_level) * 0.35

                pre_roll.append(frame_np)
                analysis_window.append(frame_f32)

                if len(analysis_window) < 10: continue

                window = np.concatenate(list(analysis_window)).astype(np.float32)
                if self._has_speech(window, threshold=0.30):
                    if not recording:
                        log_time(">>> [AUDIO] Ses algılandı...")
                        recording = True
                        collected_audio = []
                        for old_frame in pre_roll:
                            collected_audio.extend(old_frame.tolist())
                    
                    collected_audio.extend(frame_np.tolist())
                    silent_frames = 0
                elif recording:
                    collected_audio.extend(frame_np.tolist())
                    silent_frames += 1
                    
                    if silent_frames > 40: # ~1.3sn sessizlik
                        audio_data = np.array(collected_audio, dtype=np.int16)
                        if len(audio_data) > 8000:
                            log_time(">>> [VAD] Konuşma bitti, kuyruğa alınıyor...")
                            try: self.stt_queue.put_nowait(audio_data)
                            except queue.Full: pass
                        recording = False; collected_audio = []
        finally:
            if self.recorder:
                self.recorder.stop()
                self.recorder.delete()

    def _stt_worker_loop(self):
        while not self._shutting_down:
            try:
                audio_data = self.stt_queue.get(timeout=0.5)
                start_stt = time.time()
                
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                    tmp_path = tmp.name
                with wave.open(tmp_path, "wb") as wf:
                    wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(16000)
                    wf.writeframes(audio_data.tobytes())

                segments, _ = self.stt_model.transcribe(tmp_path, language=self.lang)
                text = " ".join([s.text for s in segments]).strip()
                
                try: os.remove(tmp_path)
                except: pass

                if not text or len(text) < 2: continue
                log_time(f">>> [STT] '{text}' ({time.time()-start_stt:.2f}s)")

                # Komutlar
                if any(w in text.lower() for w in ["sus", "sessiz ol", "dur"]):
                    self._muted = True
                    self.event_queue.put({"type": "sleep"})
                    continue

                if self._muted and ("hey" in text.lower()):
                    self._muted = False
                    self.event_queue.put({"type": "resumed"})
                    continue

                if not self._muted:
                    self.event_queue.put({"type": "command", "text": text})
            except queue.Empty: continue

    def speak(self, text):
        if not text: return
        log_time(f"Poodle: {text}")
        self._busy = True
        self._tts_peak_level = 0.0
        
        try:
            pcm_buffer = bytearray()
            sample_rate = self.voice.config.sample_rate

            for chunk_bytes in self.voice.synthesize_stream(text):
                if chunk_bytes:
                    # Ağız animasyonu için peak hesaplama
                    chunk_samples = np.frombuffer(chunk_bytes, dtype=np.int16).astype(np.float32) / 32768.0
                    if len(chunk_samples) > 0:
                        rms = np.sqrt(np.mean(np.square(chunk_samples)))
                        level = min(1.0, rms * 14.0)
                        if level > self._tts_peak_level: self._tts_peak_level = level
                    pcm_buffer.extend(chunk_bytes)

            if len(pcm_buffer) == 0: return

            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                temp_path = tmp.name
            with wave.open(temp_path, "wb") as wav_file:
                wav_file.setnchannels(1); wav_file.setsampwidth(2)
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(bytes(pcm_buffer))

            duration = len(pcm_buffer) / (2 * sample_rate)
            self._tts_level = max(0.15, min(1.0, self._tts_peak_level))
            self._tts_play_until = time.time() + duration

            cmd = "/usr/bin/afplay" if platform.system() == "Darwin" else "aplay"
            subprocess.run([cmd, temp_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            try: os.remove(temp_path)
            except: pass
        finally:
            self._busy = False
            self._last_tts_time = time.time()

    def get_visual_state(self):
        is_playing = time.time() < self._tts_play_until
        return {
            "input_level": self._input_level,
            "is_speaking": is_playing,
            "tts_level": self._tts_level if is_playing else 0.0
        }

    def is_muted(self): return self._muted
    def set_busy(self, val): self._busy = val
