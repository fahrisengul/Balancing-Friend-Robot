import pygame
import time
import sys

from face_ui import PoodleFace
from speech_engine import PoodleSpeech
from brain.brain import PoodleBrain
from brain.orchestrator import RobotOrchestrator


def main():
    pygame.init()
    screen = pygame.display.set_mode((1024, 600))
    pygame.display.set_caption("Poodle Robot - AI Brain")
    clock = pygame.time.Clock()

    face = PoodleFace(1024, 600)
    brain = PoodleBrain()

    # İstersen sabitle:
    # speech = PoodleSpeech(input_device_index=1)
    speech = PoodleSpeech(input_device_index=-1)
    speech.debug_list_input_devices()

    orchestrator = RobotOrchestrator(face=face, speech=speech, brain=brain)
    orchestrator.start()

    running = True
    idle_look_timer = 0

    print("\n--- Poodle Robot Zeka Katmanıyla Aktif ---")
    print("Doğal dinleme aktif. Pencereyi kapatarak çıkabilirsin.")

    try:
        while running:
            now = time.time()

            orchestrator.handle_pending_speech_events()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            mouse_pos = pygame.mouse.get_pos()
            idle_look_timer = orchestrator.update_face_idle_behavior(
                now=now,
                mouse_pos=mouse_pos,
                idle_look_timer=idle_look_timer
            )

            face.draw(screen)
            pygame.display.flip()
            clock.tick(30)

    finally:
        orchestrator.stop()
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    main()
