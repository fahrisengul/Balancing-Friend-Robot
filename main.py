import pygame
import sys

from speech_engine import PoodleSpeech
from brain.brain import PoodleBrain
from face_ui import PoodleFace
from orchestrator import Orchestrator


def main():

    pygame.init()
    screen = pygame.display.set_mode((1024, 600))
    clock = pygame.time.Clock()

    speech = PoodleSpeech()
    brain = PoodleBrain()
    face = PoodleFace()

    orch = Orchestrator(brain, speech, face)

    speech.debug_list_input_devices()
    speech.start_auto_listener()

    running = True

    print("\n--- Poodle Aktif ---\n")

    while running:

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        evt = speech.get_pending_event()
        orch.handle_event(evt)

        face.update()
        face.draw(screen)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
