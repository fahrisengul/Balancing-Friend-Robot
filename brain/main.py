import pygame
import threading
import random
import time
import sys

from face_ui import PoodleFace
from speech_engine import PoodleSpeech
from brain import PoodleBrain


def main():
    pygame.init()
    screen = pygame.display.set_mode((1024, 600))
    pygame.display.set_caption("Poodle Robot - AI Brain")
    clock = pygame.time.Clock()

    face = PoodleFace(1024, 600)
    brain = PoodleBrain()

    # Varsayılan mikrofon için -1
    # Doğrudan cihaz seçmek istersen 0 veya 1 deneyebilirsin
    speech = PoodleSpeech(input_device_index=-1)
    speech.debug_list_input_devices()

    running = True
    is_busy = False
    last_interaction_time = time.time()
    idle_look_timer = 0

    speech.start_auto_listener()

    def set_robot_busy(value: bool):
        nonlocal is_busy
        is_busy = value
        speech.set_busy(value)

    def speak_text(text: str, face_state: str = "speaking"):
        nonlocal last_interaction_time
        if not text:
            return

        set_robot_busy(True)
        try:
            face.set_state(face_state)
            speech.speak(text)
        except Exception as e:
            print(f">>> [SPEAK HATASI] {type(e).__name__}: {e}")
            face.set_state("error")
        finally:
            face.set_state("idle")
            last_interaction_time = time.time()
            set_robot_busy(False)

    def run_response(user_text: str):
        nonlocal last_interaction_time
        if not user_text:
            return

        cleaned = user_text.strip().lower()

        # LLM'e hiç gitmemesi gereken çok zayıf girdiler
        bad_inputs = {
            "hey", "poodle", "tamam", "peki", "evet", "hmm", "aba", "baba"
        }
        if cleaned in bad_inputs:
            return

        set_robot_busy(True)
        try:
            face.set_state("listening")
            poodle_response = brain.ask_poodle(user_text)

            face.set_state("speaking")
            speech.speak(poodle_response)

        except Exception as e:
            print(f">>> [MAIN HATASI] {type(e).__name__}: {e}")
            face.set_state("error")
            try:
                speech.speak("Şu an küçük bir sorun yaşadım. Bir daha söyler misin?")
            except Exception:
                pass
        finally:
            face.set_state("idle")
            last_interaction_time = time.time()
            set_robot_busy(False)

    print("\n--- Poodle Robot Zeka Katmanıyla Aktif ---")
    print("Doğal dinleme aktif. Pencereyi kapatarak çıkabilirsin.")

    try:
        while running:
            now = time.time()

            if not is_busy:
                evt = speech.get_pending_event()

                if evt["type"] == "command":
                    threading.Thread(
                        target=run_response,
                        args=(evt["text"],),
                        daemon=True
                    ).start()

                elif evt["type"] == "clarify":
                    threading.Thread(
                        target=speak_text,
                        args=(evt["text"], "error"),
                        daemon=True
                    ).start()

                elif evt["type"] == "sleep":
                    face.set_state("idle")
                    last_interaction_time = time.time()

                elif evt["type"] == "resumed":
                    face.set_state("listening")
                    last_interaction_time = time.time()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            # Görsel update
            if not is_busy:
                if speech.is_muted():
                    face.set_state("idle")
                else:
                    if now - last_interaction_time > 10:
                        if now > idle_look_timer:
                            face.update_gaze(
                                random.randint(200, 800),
                                random.randint(150, 450)
                            )
                            idle_look_timer = now + random.uniform(3, 6)
                    else:
                        mx, my = pygame.mouse.get_pos()
                        face.update_gaze(mx, my)

            face.draw(screen)
            pygame.display.flip()
            clock.tick(30)

    finally:
        speech.stop_auto_listener()
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    main()
