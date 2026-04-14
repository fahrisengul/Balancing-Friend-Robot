import time
import pygame

from brain import PoodleBrain
from speech import PoodleSpeech
from speech.pipeline import AudioPipeline
from character_ui import PoodleCharacter


def main():
    pygame.init()

    screen = pygame.display.set_mode((1024, 600))
    pygame.display.set_caption("Poodle Robot - AI Brain")
    clock = pygame.time.Clock()

    # Core components
    face = PoodleCharacter(1024, 600)
    brain = PoodleBrain()
    speech = PoodleSpeech()
    pipeline = AudioPipeline(speech=speech, brain=brain, face=face)

    # Audio setup
    speech.debug_list_input_devices()
    speech.select_default_input_device()
    speech.start_auto_listener()

    print("\n--- Poodle Robot Aktif ---")

    running = True
    last_interaction_time = time.time()
    idle_look_timer = 0.0

    while running:
        now = time.time()
        mouse_pos = pygame.mouse.get_pos()

        # Audio event
        event = speech.get_pending_event()
        if event["type"] != "none":
            pipeline.process_event(event)
            last_interaction_time = now

        # UI events
        for pg_event in pygame.event.get():
            if pg_event.type == pygame.QUIT:
                running = False

            elif pg_event.type == pygame.KEYDOWN:
                if pg_event.key == pygame.K_q:
                    running = False

                elif pg_event.key == pygame.K_SPACE:
                    pipeline.process_event({
                        "type": "command",
                        "text": "Merhaba"
                    })
                    last_interaction_time = time.time()

        # Face updates
        if hasattr(face, "update"):
            face.update()

        if hasattr(face, "update_gaze"):
            face.update_gaze(*mouse_pos)

        # Idle behavior
        if now - last_interaction_time > 8:
            idle_look_timer += clock.get_time() / 1000.0
            if idle_look_timer > 2.0:
                idle_look_timer = 0.0
                if hasattr(face, "set_state"):
                    face.set_state("idle")

        # Draw
        if hasattr(face, "draw"):
            face.draw(screen)

        pygame.display.flip()
        clock.tick(30)

    # Shutdown
    speech.stop_auto_listener()
    pygame.quit()


if __name__ == "__main__":
    main()
