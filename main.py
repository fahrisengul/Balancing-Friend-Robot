import pygame
import sys

from speech_engine import PoodleSpeech
from brain.brain import PoodleBrain
from character_ui import PoodleCharacter
from orchestrator import Orchestrator


def main():
    pygame.init()
    screen = pygame.display.set_mode((1024, 600))
    pygame.display.set_caption("Poodle Robot")
    clock = pygame.time.Clock()

    # Jabra SPEAK 510 USB = #0
    speech = PoodleSpeech(input_device_index=0)
    brain = PoodleBrain()
    face = PoodleCharacter(1024, 600)
    face.bind_audio_source(speech)

    orch = Orchestrator(brain, speech, face)

    speech.debug_list_input_devices()
    speech.start_auto_listener()

    print("\n--- Poodle Aktif ---\n")

    running = True
    last_ticks = pygame.time.get_ticks()

    try:
        while running:
            now_ticks = pygame.time.get_ticks()
            dt = max(0.001, (now_ticks - last_ticks) / 1000.0)
            last_ticks = now_ticks

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    running = False

            evt = speech.get_pending_event()
            orch.handle_event(evt)

            face.update(dt)
            face.draw(screen)

            pygame.display.flip()
            clock.tick(60)

    finally:
        print(">>> [SHUTDOWN] Sistem kapatılıyor...")

        try:
            orch.stop()
        except Exception:
            pass

        try:
            speech.stop_auto_listener()
        except Exception as e:
            print(f">>> [SHUTDOWN ERROR - SPEECH] {e}")

        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    main()
