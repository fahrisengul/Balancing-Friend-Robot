import pygame
import threading
import random
import time

from face_ui import PoodleFace
from speech_engine import PoodleSpeech
from brain import PoodleBrain

brain = PoodleBrain()


def main():
    pygame.init()
    screen = pygame.display.set_mode((1024, 600))
    pygame.display.set_caption("Poodle Robot - Llama-3 Brain")
    clock = pygame.time.Clock()

    face = PoodleFace(1024, 600)

    # Harici mikrofonu kullanmak istersen:
    # speech = PoodleSpeech(input_device="FahriSengul Mikrofonu")
    speech = PoodleSpeech()
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

    def run_response(user_text):
        nonlocal last_interaction_time

        if not user_text:
            return

        bad_inputs = {"hey", "aba", "tamam", "peki", "hmm"}
        if user_text.strip().lower() in bad_inputs:
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
            speech.speak("Bir sorun yaşadım Tanem.")

        finally:
            face.set_state("idle")
            last_interaction_time = time.time()
            set_robot_busy(False)

    print("\n--- Poodle Robot Zeka Katmanıyla Aktif ---")
    print("Doğal dinleme aktif. Pencereyi kapatarak çıkabilirsin.")

    while running:
        now = time.time()
        mouse_pos = pygame.mouse.get_pos()

        if not is_busy:
            evt = speech.get_pending_event()

            if evt["type"] == "command":
                threading.Thread(
                    target=run_response,
                    args=(evt["text"],),
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

        if not is_busy:
            if speech.is_muted():
                face.set_state("idle")
            else:
                if now - last_interaction_time > 10:
                    if now > idle_look_timer:
                        rx = random.randint(200, 800)
                        ry = random.randint(150, 450)
                        face.update_gaze(rx, ry)
                        idle_look_timer = now + random.uniform(3, 6)
                else:
                    face.update_gaze(mouse_pos[0], mouse_pos[1])

        face.draw(screen)
        pygame.display.flip()
        clock.tick(60)

    speech.stop_auto_listener()
    pygame.quit()


if __name__ == "__main__":
    main()
