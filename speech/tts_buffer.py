import threading
import queue
import time


class TTSBuffer:
    def __init__(self, owner):
        self.owner = owner
        self.queue = queue.Queue()
        self._running = True

        # duplicate engelleme için
        self._last_text = None

        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    # -----------------------------
    # EXTERNAL CALL
    # -----------------------------
    def speak(self, text):
        if not text:
            return

        # aynı text'i arka arkaya basmayı engelle
        if text == self._last_text:
            print(">>> [TTS BUFFER] duplicate ignored:", text)
            return

        print(">>> [TTS BUFFER] enqueue:", text)
        self.queue.put(text)

    # -----------------------------
    # INTERNAL LOOP
    # -----------------------------
    def _loop(self):
        while self._running:
            try:
                text = self.queue.get()

                print(">>> [TTS BUFFER] dequeued:", text)

                # konuşma bitene kadar bekle (CPU yakmadan)
                while getattr(self.owner, "_speaking", False):
                    time.sleep(0.01)

                # state set
                self._last_text = text

                # SPEAK
                self.owner._speak_now(text)

            except Exception as e:
                print(f">>> [TTS BUFFER ERROR] {e}")

    # -----------------------------
    # STOP (opsiyonel)
    # -----------------------------
    def stop(self):
        self._running = False
