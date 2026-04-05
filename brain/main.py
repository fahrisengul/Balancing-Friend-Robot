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

    running = True
    is_busy = False
    last_interaction_time = time.time()
    idle_look_timer = 0

    def run_speak(text):
        nonlocal is_busy, last_interaction_time
        try:
            is_busy = True
            face.set_state("speaking")
            speech.speak(text)
        finally:
            face.set_state("idle")
            last_interaction_time = time.time()
            is_busy = False

    def voice_interaction_direct():
        """
        Manuel tetikleme:
        L tuşuna basınca wake word beklemeden direkt komut dinler.
        """
        nonlocal last_interaction_time, is_busy

        if is_busy:
            return

        is_busy = True

        try:
            face.set_state("listening")
            user_text = speech.listen_command_vad()

            if user_text:
                face.set_state("thinking")
                poodle_response = brain.ask_poodle(user_text)

                face.set_state("speaking")
                speech.speak(poodle_response)
            else:
                face.set_state("error")
                speech.speak("Seni tam duyamadım Tanem, tekrar söyler misin?")

        except Exception as e:
            print(f">>> [MAIN HATASI] {e}")
            face.set_state("error")
            speech.speak("Bir sorun yaşadım Tanem.")

        finally:
            face.set_state("idle")
            last_interaction_time = time.time()
            is_busy = False

    def voice_interaction_wakeword():
        """
        İstersen bunu ileride sürekli dinleme modu için kullanabilirsin.
        Wake word bekler, sonra komutu alır.
        """
        nonlocal last_interaction_time, is_busy

        if is_busy:
            return

        is_busy = True

        try:
            face.set_state("listening")
            user_text = speech.listen()

            if user_text:
                face.set_state("thinking")
                poodle_response = brain.ask_poodle(user_text)

                face.set_state("speaking")
                speech.speak(poodle_response)
            else:
                face.set_state("error")
                speech.speak("Seni tam duyamadım Tanem, tekrar söyler misin?")

        except Exception as e:
            print(f">>> [MAIN HATASI] {e}")
            face.set_state("error")
            speech.speak("Bir sorun yaşadım Tanem.")

        finally:
            face.set_state("idle")
            last_interaction_time = time.time()
            is_busy = False

    print("\n--- Poodle Robot Zeka Katmanıyla Aktif ---")
    print("L: Direkt Dinleme | W: Wake Word Modu | SPACE: Selamla | Q: Çıkış")

    while running:
        now = time.time()
        mouse_pos = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN and not is_busy:
                if event.key == pygame.K_l:
                    threading.Thread(target=voice_interaction_direct, daemon=True).start()

                elif event.key == pygame.K_w:
                    threading.Thread(target=voice_interaction_wakeword, daemon=True).start()

                elif event.key == pygame.K_SPACE:
                    greeting = brain.ask_poodle("Merhaba")
                    threading.Thread(target=run_speak, args=(greeting,), daemon=True).start()

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

    pygame.quit()


if __name__ == "__main__":
    main()
