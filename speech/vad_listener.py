from collections import deque
import threading

import numpy as np
import torch
from pvrecorder import PvRecorder
from silero_vad import get_speech_timestamps


class RollingVADListener:
    def __init__(self, owner):
        self.owner = owner

    def segment_has_speech(self, audio_float32: np.ndarray) -> bool:
        if len(audio_float32) == 0:
            return False

        try:
            audio_tensor = torch.from_numpy(audio_float32)
            speech_ts = get_speech_timestamps(
                audio_tensor,
                self.owner.vad_model,
                sampling_rate=self.owner.sample_rate,
                threshold=0.12,
            )
            return len(speech_ts) > 0
        except Exception as e:
            if self.owner.DEBUG_AUDIO:
                self.owner.log_time(f">>> [SEGMENT VAD ERROR] {type(e).__name__}: {e}")
            return float(np.max(np.abs(audio_float32))) >= 0.08

    def listener_loop(self):
        recorder = None

        prebuffer_frames = 12
        min_voiced_frames_to_start = 4
        silence_frames_to_stop = 18
        max_segment_frames = 260

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
            self.owner.log_time(f">>> [LISTENER] Thread başladı. device_index={self.owner.device_index}")

            recorder = PvRecorder(
                device_index=self.owner.device_index if self.owner.device_index is not None else -1,
                frame_length=self.owner.frame_length,
            )
            recorder.start()

            with self.owner._recorder_lock:
                self.owner.recorder = recorder

            self.owner.log_time(">>> [LISTENER] PvRecorder başlatıldı.")

            while self.owner._listener_running:
                try:
                    frame = recorder.read()
                except Exception as e:
                    self.owner.log_time(f">>> [RECORDER READ ERROR] {type(e).__name__}: {e}")
                    break

                if not self.owner._listener_running:
                    break

                audio_float32 = np.array(frame, dtype=np.float32) / 32768.0
                audio_float32 = audio_float32 * 2.0

                level = float(np.max(np.abs(audio_float32)))
                frame_counter += 1

                if self.owner.DEBUG_AUDIO and frame_counter % 8 == 0:
                    self.owner.log_time(f">>> [AUDIO RAW] level={level:.4f}")

                if self.owner._busy and not recording:
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
                        collected_frames = list(prebuffer)
                        self.owner.log_time(">>> [AUDIO] Ses algılandı (rolling VAD tetiklendi)...")
                    continue

                collected_frames.append(audio_float32.copy())

                if level >= speech_continue_level:
                    silence_run = 0
                else:
                    silence_run += 1

                segment_too_long = len(collected_frames) >= max_segment_frames
                silence_finished = silence_run >= silence_frames_to_stop

                if silence_finished or segment_too_long:
                    segment_audio = np.concatenate(collected_frames).astype(np.float32)
                    duration_sec = len(segment_audio) / float(self.owner.sample_rate)

                    valid_speech = False
                    if duration_sec >= min_segment_sec:
                        valid_speech = self.segment_has_speech(segment_audio)

                    if valid_speech:
                        self.owner.log_time(">>> [VAD] Konuşma bitti, STT başlıyor...")
                        audio_int16 = np.clip(segment_audio, -1.0, 1.0)
                        audio_int16 = (audio_int16 * 32767.0).astype(np.int16)

                        threading.Thread(
                            target=self.owner._process_speech,
                            args=(audio_int16,),
                            daemon=True
                        ).start()
                    else:
                        if self.owner.DEBUG_AUDIO:
                            self.owner.log_time(">>> [VAD] Segment toplandı ama konuşma doğrulanamadı.")

                    recording = False
                    voiced_run = 0
                    silence_run = 0
                    collected_frames = []
                    prebuffer.clear()

        except Exception as e:
            self.owner.log_time(f">>> [RECORDER ERROR] {type(e).__name__}: {e}")

        finally:
            cleanup_recorder = None

            with self.owner._recorder_lock:
                if self.owner.recorder is recorder:
                    cleanup_recorder = self.owner.recorder
                    self.owner.recorder = None

            if cleanup_recorder is not None:
                try:
                    cleanup_recorder.stop()
                except Exception:
                    pass

                try:
                    cleanup_recorder.delete()
                except Exception:
                    pass

            self.owner.log_time(">>> [LISTENER] Thread durdu.")
