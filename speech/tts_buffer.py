import threading
import queue


class TTSBuffer:
    def __init__(self, owner):
        self.owner = owner
        self.queue = queue.Queue()
        self._running = True

        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    # -----------------------------
    # EXTERNAL CALL
    # -----------------------------
    def speak(self, text):
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

                # KONUSUYORSA BEKLE
                while self.owner._speaking:
                    pass

                self.owner._speak_now(text)

            except Exception as e:
                print(f">>> [TTS BUFFER ERROR] {e}")

    # -----------------------------
    # STOP (opsiyonel)
    # -----------------------------
    def stop(self):
        self._running = False
