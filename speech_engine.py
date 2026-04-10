import queue
import threading
import sounddevice as sd
import numpy as np
import time

class PoodleSpeech:
    def __init__(self, device_index=None):
        self.event_queue = queue.Queue()
        self.running = False

        self.device_index = device_index
        self.sample_rate = 16000

        self.audio_queue = queue.Queue()
        self.worker_thread = None

    # -------------------------
    # DEVICE DEBUG
    # -------------------------
    def debug_list_input_devices(self):
        print(">>> [MIC DEBUG] Cihaz Listesi:")
        devices = sd.query_devices()
        for i, dev in enumerate(devices):
            if dev["max_input_channels"] > 0:
                print(f"    #{i}: {dev['name']}")

    def set_input_device_by_name(self, keyword: str):
        devices = sd.query_devices()
        for i, dev in enumerate(devices):
            if keyword.lower() in dev["name"].lower():
                self.device_index = i
                print(f">>> [MIC] Seçilen cihaz: {dev['name']}")
                return
        print(">>> [MIC] Cihaz bulunamadı, default kullanılacak.")

    # -------------------------
    # AUDIO CALLBACK
    # -------------------------
    def _audio_callback(self, indata, frames, time_info, status):
        if not self.running:
            return

        volume_norm = np.linalg.norm(indata) * 10

        # Basit VAD threshold
        if volume_norm > 0.5:
            print(f"[{self._now()}] >>> [AUDIO] Ses algılandı (VAD tetiklendi)...")
            self.audio_queue.put(indata.copy())

    # -------------------------
    # STT WORKER
    # -------------------------
    def _stt_worker(self):
        print(">>> [STT WORKER] Hazır.")
        while self.running:
            try:
                data = self.audio_queue.get(timeout=1)
            except queue.Empty:
                continue

            text = self._fake_stt(data)

            if text:
                print(f"[{self._now()}] >>> [STT] '{text}'")
                self.event_queue.put({"type": "speech", "text": text})

        print(">>> [STT WORKER] Durdu.")

    # -------------------------
    # FAKE STT (placeholder)
    # -------------------------
    def _fake_stt(self, data):
        # burada whisper olacak ileride
        return "Selam."

    # -------------------------
    # LISTENER
    # -------------------------
    def start_auto_listener(self):
        self.running = True

        self.stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=1,
            callback=self._audio_callback,
            device=self.device_index,
        )

        self.stream.start()

        self.worker_thread = threading.Thread(target=self._stt_worker, daemon=True)
        self.worker_thread.start()

    def stop_auto_listener(self):
        self.running = False

        try:
            if self.stream:
                self.stream.stop()
                self.stream.close()
        except:
            pass

        if self.worker_thread:
            self.worker_thread.join(timeout=2)

    # -------------------------
    # EVENTS
    # -------------------------
    def get_pending_event(self):
        try:
            return self.event_queue.get_nowait()
        except queue.Empty:
            return None

    # -------------------------
    # UTIL
    # -------------------------
    def _now(self):
        return time.strftime("%H:%M:%S", time.localtime())
