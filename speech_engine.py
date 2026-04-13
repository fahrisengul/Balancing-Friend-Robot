import os
import wave
import tempfile
import threading
import platform
import subprocess
import time
from datetime import datetime
from collections import deque

from pvrecorder import PvRecorder
import numpy as np
import torch
from faster_whisper import WhisperModel
from piper.voice import PiperVoice
from silero_vad import load_silero_vad, get_speech_timestamps


DEBUG_AUDIO = False


def get_now():
    return datetime.now().strftime("%H:%M:%S.%f")[:-3]


def log_time(message: str):
    print(f"[{get_now()}] {message}")


class PoodleSpeech:
    def __init__(self, lang: str = "tr", input_device_index=None):
        self.lang = lang
        self.frame_length = 512
        self.sample_rate = 16000

        self.event_queue = []

        self._listener_running = False
        self._busy = False
        self._muted = False

        self.recorder = None
        self.listener_thread = None
        self._recorder_lock = threading.Lock()

        self.device_index = input_device_index

        # TTS phrase buffer
        self._pending_phrase = ""
        self._pending_phrase_since = 0.0
        self._min_phrase_chars = 28
        self._max_phrase_wait_sec = 0.7
        self._last_tts_time = 0.0
        self._tts_cooldown_sec = 0.65

        log_time(">>> Modeller yükleniyor (Whisper/VAD/Piper)...")
        self.stt_model = WhisperModel("base", device="cpu", compute_type="int8")
        self.vad_model = load_silero_vad()
        self.voice = PiperVoice.load("tr_TR-fahrettin-medium.onnx")
        log_time(">>> [SES] Tüm sistemler hazır.")

    # =========================================================
    # DEVICE / DEBUG
    # =========================================================
    def debug_list_input_devices(self):
        try:
            devices = PvRecorder.get_available_devices()
            log_time(">>> [MIC DEBUG] Cihaz Listesi:")
            for i, name in enumerate(devices):
                print(f"    #{i}: {name}")
        except Exception as e:
            log_time(f">>> [MIC DEBUG ERROR] {type(e).__name__}: {e}")

    def select_default_input_device(self):
        try:
            devices = PvRecorder.get_available_devices()

            # Manuel seçim geldiyse onu kullan
            if self.device_index is not None and self.device_index >= 0:
                if self.device_index < len(devices):
                    log_time(f">>> [MIC ACTIVE] Manuel seçim: #{self.device_index} {devices[self.device_index]}")
                    return self.device_index

            if not devices:
                self.device_index = -1
                log_time(">>> [MIC ACTIVE] Kayıt cihazı bulunamadı, default (-1) kullanılacak.")
                return self.device_index

            # Otomatik seçim: mikrofon benzeri isimleri öne al
            preferred_idx = None
            preferred_keywords = [
                "mikrofon",
                "microphone",
                "macbook pro mikrofonu",
                "internal",
                "built-in",
            ]
            avoid_keywords = [
                "speaker",
                "hoparlor",
                "hoparlör",
                "output",
                "kulaklik cikisi",
                "kulaklık çıkışı",
            ]

            for i, name in enumerate(devices):
                low = name.lower()

                if any(bad in low for bad in avoid_keywords):
                    continue

                if any(key in low for key in preferred_keywords):
                    preferred_idx = i
                    break

            if preferred_idx is None:
                preferred_idx = 0

            self.device_index = preferred_idx
            log_time(f">>> [MIC ACTIVE] Otomatik seçim: #{preferred_idx} {devices[preferred_idx]}")
            return self.device_index

        except Exception as e:
            log_time(f">>> [MIC SELECT ERROR] {type(e).__name__}: {e}")
            self.device_index = -1
            return self.device_index

    # =========================================================
    # STATE
    # =========================================================
    def is_muted(self):
        return self._muted

    def set_busy(self, val: bool):
        self._busy = val

    # =========================================================
    # AUTO LISTENER
    # =========================================================
    def start_auto_listener(self):
        if self._listener_running:
            return

        if self.device_index is None or self.device_index < 0:
            self.select_default_input_device()

        self._listener_running = True
        self.listener_thread = threading.Thread(target=self._listener_loop, daemon=True)
        self.listener_thread.start()
        log_time("[DINLEME MODU] Arka plan dinlemesi aktif.")

    def stop_auto_listener(self):
        self._listener_running = False

        if self.listener_thread and self.listener_thread.is_alive():
            self.listener_thread.join(timeout=2.0)

        recorder_to_cleanup = None
        with self._recorder_lock:
            if self.recorder is not None:
                recorder_to_cleanup = self.recorder
                self.recorder = None

        if recorder_to_cleanup is not None:
            try:
                recorder_to_cleanup.stop()
            except Exception:
                pass

            try:
                recorder_to_cleanup.delete()
            except Exception:
                pass

        self.listener_thread = None

    def get_pending_event(self):
        if len(self.event_queue) > 0:
            return self.event_queue.pop(0)
        return {"type": "none"}

    # =========================================================
    # LISTENER LOOP (ROLLING-BUFFER VAD)
    # =========================================================
    def _listener_loop(self):
        recorder = None

        # Rolling-buffer / segmentation tuning
        prebuffer_frames = 12              # yaklaşık 12 * 32ms ≈ 384ms
        min_voiced_frames_to_start = 4     # konuşmayı başlatmak için
        silence_frames_to_stop = 18        # yaklaşık 576ms sessizlik
        max_segment_frames = 260           # yaklaşık 8.3 saniye üst sınır

        speech_start_level = 0.055
        speech_continue_level = 0.028
        min_segment_sec = 0.45

        prebuffer = deque(maxlen=prebuffer_frames)
        collected_frames = []
        recording = False
        voiced_run = 0
        silence_run = 0
        frame_counter = 0

        try:
            log_time(f">>> [LISTENER] Thread başladı. device_index={self.device_index}")

            recorder = PvRecorder(
                device_index=self.device_index if self.device_index is not None else -1,
                frame_length=self.frame_length,
            )
            recorder.start()

            with self._recorder_lock:
                self.recorder = recorder

            log_time(">>> [LISTENER] PvRecorder başlatıldı.")

            while self._listener_running:
                try:
                    frame = recorder.read()
                except Exception as e:
                    log_time(f">>> [RECORDER READ ERROR] {type(e).__name__}: {e}")
                    break

                if not self._listener_running:
                    break

                audio_float32 = np.array(frame, dtype=np.float32) / 32768.0
                audio_float32 = audio_float32 * 2.0  # hafif gain

                level = float(np.max(np.abs(audio_float32)))
                frame_counter += 1

                if DEBUG_AUDIO and frame_counter % 8 == 0:
                    log_time(f">>> [AUDIO RAW] level={level:.4f}")

                # Robot konuşurken yeni kayıt başlatma
                if self._busy and not recording:
                    continue

                prebuffer.append(audio_float32.copy())

                if not recording:
                    if level >= speech_start_level:
                        voiced_run += 1
                    else:
                        voiced_run = max(0, voiced_run - 1)

                    if voiced_run >= min_voiced_frames_to_start:
                        recording = True
                        silence_run = 0

                        # konuşma başlarken prebuffer'ı da ekle
                        collected_frames = list(prebuffer)

                        log_time(">>> [AUDIO] Ses algılandı (rolling VAD tetiklendi)...")
                    continue

                # recording=True
                collected_frames.append(audio_float32.copy())

                if level >= speech_continue_level:
                    silence_run = 0
                else:
                    silence_run += 1

                segment_too_long = len(collected_frames) >= max_segment_frames
                silence_finished = silence_run >= silence_frames_to_stop

                if silence_finished or segment_too_long:
                    segment_audio = np.concatenate(collected_frames).astype(np.float32)

                    duration_sec = len(segment_audio) / float(self.sample_rate)

                    # son bir Silero doğrulaması: artık küçük frame değil, segment bazlı
                    valid_speech = False
                    if duration_sec >= min_segment_sec:
                        valid_speech = self._segment_has_speech(segment_audio)

                    if valid_speech:
                        log_time(">>> [VAD] Konuşma bitti, STT başlıyor...")
                        audio_int16 = np.clip(segment_audio, -1.0, 1.0)
                        audio_int16 = (audio_int16 * 32767.0).astype(np.int16)

                        threading.Thread(
                            target=self._process_speech,
                            args=(audio_int16,),
                            daemon=True
                        ).start()
                    else:
                        if DEBUG_AUDIO:
                            log_time(">>> [VAD] Segment toplandı ama konuşma doğrulanamadı.")

                    # reset
                    recording = False
                    voiced_run = 0
                    silence_run = 0
                    collected_frames = []
                    prebuffer.clear()

        except Exception as e:
            log_time(f">>> [RECORDER ERROR] {type(e).__name__}: {e}")

        finally:
            cleanup_recorder = None
            with self._recorder_lock:
                if self.recorder is recorder:
                    cleanup_recorder = self.recorder
                    self.recorder = None

            if cleanup_recorder is not None:
                try:
                    cleanup_recorder.stop()
                except Exception:
                    pass

                try:
                    cleanup_recorder.delete()
                except Exception:
                    pass

            log_time(">>> [LISTENER] Thread durdu.")

    def _segment_has_speech(self, audio_float32: np.ndarray) -> bool:
        if len(audio_float32) == 0:
            return False

        try:
            audio_tensor = torch.from_numpy(audio_float32)
            speech_ts = get_speech_timestamps(
                audio_tensor,
                self.vad_model,
                sampling_rate=self.sample_rate,
                threshold=0.12,
            )
            return len(speech_ts) > 0
        except Exception as e:
            if DEBUG_AUDIO:
                log_time(f">>> [SEGMENT VAD ERROR] {type(e).__name__}: {e}")
            # fallback: energy üzerinden kabul et
            return float(np.max(np.abs(audio_float32))) >= 0.08

    # =========================================================
    # STT
    # =========================================================
    def _process_speech(self, audio_int16: np.ndarray):
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            with wave.open(tmp_path, "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(self.sample_rate)
                wf.writeframes(audio_int16.tobytes())

            segments, _ = self.stt_model.transcribe(tmp_path, language=self.lang)
            text = " ".join([s.text for s in segments]).strip()

        finally:
            try:
                os.remove(tmp_path)
            except Exception:
                pass

        if not text or len(text) < 2:
            return

        log_time(f">>> [STT] '{text}'")

        lowered = text.lower()

        if any(w in lowered for w in ["sus", "sessiz ol", "dur"]):
            self._muted = True
            log_time(">>> [MODE] Sessiz mod.")
            self.event_queue.append({"type": "sleep"})
            return

        if self._muted and any(w in lowered for w in ["uyan", "devam et", "konuşabilirsin", "hey"]):
            self._muted = False
            log_time(">>> [MODE] Aktif mod.")
            self.event_queue.append({"type": "resumed"})
            return

        if not self._muted:
            self.event_queue.append({"type": "command", "text": text})

    # =========================================================
    # TTS
    # =========================================================
    def speak(self, text: str):
        cleaned = self._clean_tts_text(text)
        if not cleaned:
            return

        now = time.time()

        if self._should_hold_phrase(cleaned):
            if not self._pending_phrase:
                self._pending_phrase = cleaned
                self._pending_phrase_since = now
                return

            merged = f"{self._pending_phrase} {cleaned}".strip()
            self._pending_phrase = self._clean_tts_text(merged)

            if (
                len(self._pending_phrase) >= self._min_phrase_chars
                or self._pending_phrase.endswith((".", "!", "?"))
                or (now - self._pending_phrase_since) >= self._max_phrase_wait_sec
            ):
                self._speak_now(self._pending_phrase)
                self._pending_phrase = ""
                self._pending_phrase_since = 0.0
            return

        if self._pending_phrase:
            combined = f"{self._pending_phrase} {cleaned}".strip()
            cleaned = self._clean_tts_text(combined)
            self._pending_phrase = ""
            self._pending_phrase_since = 0.0

        self._speak_now(cleaned)

    def flush_pending_tts(self):
        if self._pending_phrase:
            text = self._clean_tts_text(self._pending_phrase)
            self._pending_phrase = ""
            self._pending_phrase_since = 0.0
            if text:
                self._speak_now(text)

    def _should_hold_phrase(self, text: str) -> bool:
        if not text:
            return False
        if text.endswith((".", "!", "?")):
            return False
        if text.endswith(","):
            return True
        if len(text) < self._min_phrase_chars:
            return True
        if len(text.split()) < 5:
            return True
        return False

    def _clean_tts_text(self, text: str) -> str:
        text = (text or "").replace("\n", " ").strip()
        text = " ".join(text.split())

        if not text:
            return ""

        if text in {",", ".", "!", "?", ";", ":"}:
            return ""

        if len(text.split()) == 1 and not text.endswith((".", "!", "?")):
            return ""

        return text

    
    def _speak_now(self, text: str):
        if not text:
            return
    
        log_time(f"Poodle: {text}")
        self._busy = True
    
        try:
            now = time.time()
            delta = now - self._last_tts_time
            if delta < self._tts_cooldown_sec:
                time.sleep(self._tts_cooldown_sec - delta)
    
            # 🔥 Piper doğru kullanım (numpy audio üret)
            audio = self.voice.synthesize(text)
    
            # 🔥 WAV'e kendimiz yaz
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                temp_path = tmp.name
    
            with wave.open(temp_path, "wb") as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(self.voice.config.sample_rate)
                wav_file.writeframes((audio * 32767).astype("int16").tobytes())
    
            # 🔥 MAC için garanti playback
            subprocess.run(["afplay", temp_path])
    
            self._last_tts_time = time.time()
    
        except Exception as e:
            log_time(f">>> [TTS ERROR] {e}")
    
        finally:
            try:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            except:
                pass
    
            self._busy = False
