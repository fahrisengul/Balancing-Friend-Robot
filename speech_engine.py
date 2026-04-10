import threading
import queue
import time
import json

# ... (mevcut importların kalsın)

class SpeechEngine:

    def __init__(self, ...):
        # ...
        self.stt_queue = queue.Queue(maxsize=2)   # 🔥 sınır koyduk
        self._running = True
        self._busy = False

        self.worker = threading.Thread(target=self._stt_worker, daemon=True)
        self.worker.start()

    # -----------------------------
    # QUEUE FLUSH
    # -----------------------------
    def _flush_stt_queue(self):
        flushed = 0
        while True:
            try:
                self.stt_queue.get_nowait()
                flushed += 1
            except queue.Empty:
                break
        if flushed:
            print(f">>> [STT QUEUE] Temizlendi ({flushed})")

    # -----------------------------
    # AUDIO CALLBACK (VAD sonrası)
    # -----------------------------
    def _on_audio_segment(self, audio_data):
        if self._busy:
            return  # 🔥 konuşurken yeni segment alma

        try:
            self.stt_queue.put_nowait((time.time(), audio_data))
            print(f">>> [STT QUEUE] Segment eklendi. samples={len(audio_data)}")

        except queue.Full:
            try:
                self.stt_queue.get_nowait()
                print(">>> [STT QUEUE] Eski segment atıldı")
            except queue.Empty:
                pass

            try:
                self.stt_queue.put_nowait((time.time(), audio_data))
            except:
                print(">>> [STT QUEUE] Segment tamamen atlandı")

    # -----------------------------
    # STT WORKER
    # -----------------------------
    def _stt_worker(self):
        print(">>> [STT WORKER] Hazır.")

        while self._running:
            try:
                item = self.stt_queue.get(timeout=0.5)
            except queue.Empty:
                continue

            if item is None:
                break

            queued_at, audio = item

            # 🔥 bayat segment at
            if time.time() - queued_at > 2.5:
                print(">>> [STT WORKER] Bayat segment atlandı")
                continue

            try:
                text = self._transcribe(audio)

                if not text or not text.strip():
                    print(">>> [STT] Boş transkript")
                    continue

                norm = self._normalize(text)

                # 🔥 PROMPT LEAKAGE FILTER
                if self._looks_like_prompt_leakage(norm):
                    print(">>> [STT] Prompt leakage atlandı")
                    continue

                print(f">>> [STT] '{text}'")

                self._emit(text)

            except Exception as e:
                print(f">>> [STT ERROR] {e}")

        print(">>> [STT WORKER] Durdu.")

    # -----------------------------
    # SPEAK
    # -----------------------------
    def speak(self, text):
        self._busy = True
        self._flush_stt_queue()  # 🔥 konuşma öncesi temizle

        try:
            # mevcut TTS kodun
            self._tts(text)

        finally:
            time.sleep(0.2)
            self._busy = False

    # -----------------------------
    # LEAKAGE DETECTOR
    # -----------------------------
    def _looks_like_prompt_leakage(self, t):
        markers = [
            "kisa ve dogal cumleler",
            "kisa dogal diyalog",
            "robotun adi poodle",
            "turkce gunluk konusma"
        ]
        return any(m in t for m in markers)

    def stop(self):
        self._running = False
        try:
            self.stt_queue.put_nowait(None)
        except:
            pass
        self.worker.join(timeout=2)
