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
    speech = PoodleSpeech()
    speech.debug_list_input_devices()

    running = True
    is_busy = False
    last_interaction_time = time.time()
    idle_look_timer = 0

    speech.start_wake_listener()

    def set_robot_busy(value: bool):
        nonlocal is_busy
        is_busy = value
        speech.set_busy(value)

    def run_response(user_text):
        nonlocal last_interaction_time

        if not user_text:
            set_robot_busy(True)
            try:
                face.set_state("error")
                speech.speak("Seni tam duyamadım Tanem, tekrar söyler misin?")
            finally:
                face.set_state("idle")
                last_interaction_time = time.time()
                set_robot_busy(False)
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

    def manual_voice_interaction():
        nonlocal last_interaction_time

        if is_busy:
            return

        set_robot_busy(True)
        speech.pause_wake_listener(6.0)

        try:
            face.set_state("listening")
            user_text = speech.listen_once()

            if user_text:
                face.set_state("listening")
                poodle_response = brain.ask_poodle(user_text)

                face.set_state("speaking")
                speech.speak(poodle_response)
            else:
                face.set_state("error")
                speech.speak("Seni tam duyamadım Tanem, tekrar söyler misin?")

        except Exception as e:
            print(f">>> [MAIN HATASI] {type(e).__name__}: {e}")
            face.set_state("error")
            speech.speak("Bir sorun yaşadım Tanem.")

        finally:
            face.set_state("idle")
            last_interaction_time = time.time()
            set_robot_busy(False)

    def quick_greeting():
        nonlocal last_interaction_time

        if is_busy:
            return

        set_robot_busy(True)
        try:
            face.set_state("speaking")
            greeting = brain.ask_poodle("Merhaba")
            speech.speak(greeting)
        finally:
            face.set_state("idle")
            last_interaction_time = time.time()
            set_robot_busy(False)

    print("\n--- Poodle Robot Zeka Katmanıyla Aktif ---")
    print("Wake word arka planda aktif.")
    print("L: Direkt Dinleme | SPACE: Selamla | Q: Çıkış")

    while running:
        now = time.time()
        mouse_pos = pygame.mouse.get_pos()

        if not is_busy:
            pending = speech.get_pending_command()
            if pending["type"] == "command":
                threading.Thread(
                    target=run_response,
                    args=(pending["text"],),
                    daemon=True
                ).start()
            elif pending["type"] == "empty":
                threading.Thread(
                    target=run_response,
                    args=(None,),
                    daemon=True
                ).start()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN and not is_busy:
                if event.key == pygame.K_l:
                    threading.Thread(target=manual_voice_interaction, daemon=True).start()
                elif event.key == pygame.K_SPACE:
                    threading.Thread(target=quick_greeting, daemon=True).start()
                elif event.key == pygame.K_q:
                    running = False

        if not is_busy:
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

    speech.stop_wake_listener()
    pygame.quit()


if __name__ == "__main__":
    main()
