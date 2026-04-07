import pygame
import sys

from speech_engine import PoodleSpeech
from brain.brain import PoodleBrain
from face_ui import PoodleFace
from orchestrator import Orchestrator


def main():
    pygame.init()
    screen = pygame.display.set_mode((1024, 600))
    pygame.display.set_caption("Poodle Robot")
    clock = pygame.time.Clock()

    speech = PoodleSpeech()
    brain = PoodleBrain()
    face = PoodleFace()
    orch = Orchestrator(brain, speech, face)

    speech.debug_list_input_devices()
    speech.start_auto_listener()

    print("\n--- Poodle Aktif ---")
    print("ESC: çıkış\n")

    running = True

    try:
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False

            evt = speech.get_pending_event()
            orch.handle_event(evt)

            face.draw(screen)
            pygame.display.flip()
            clock.tick(60)

    finally:
        print(">>> [SHUTDOWN] Sistem kapatılıyor...")

        try:
            speech.stop_auto_listener()
        except Exception as e:
            print(f">>> [SHUTDOWN ERROR - SPEECH] {e}")

        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    main()
