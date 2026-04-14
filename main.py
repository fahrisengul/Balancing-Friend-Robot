import time
import pygame

from brain import PoodleBrain
from speech import PoodleSpeech
from speech.pipeline import AudioPipeline
from character_ui import PoodleCharacter


def boot_log(msg: str):
    print(f"[BOOT] {msg}", flush=True)


def main():
    pygame.init()

    screen = pygame.display.set_mode((1024, 600))

    pygame.display.set_caption("Poodle Robot - AI Brain")
    clock = pygame.time.Clock()

    face = PoodleCharacter(1024, 600)

    brain = PoodleBrain()

    speech = PoodleSpeech()

    pipeline = AudioPipeline(speech=speech, brain=brain, face=face)

    speech.debug_list_input_devices()

    speech.select_default_input_device()

    speech.start_auto_listener()

    print("\n--- Poodle Robot Aktif ---", flush=True)

    running = True
    last_interaction_time = time.time()
    idle_look_timer = 0.0

    while running:
        now = time.time()
        mouse_pos = pygame.mouse.get_pos()

        event = speech.get_pending_event()
        if event["type"] != "none":
            pipeline.process_event(event)
            last_interaction_time = now

        for pg_event in pygame.event.get():
            if pg_event.type == pygame.QUIT:
                running = False
            elif pg_event.type == pygame.KEYDOWN:
                if pg_event.key == pygame.K_q:
                    running = False
                elif pg_event.key == pygame.K_SPACE:
                    boot_log("manual SPACE command")
                    pipeline.process_event({"type": "command", "text": "Merhaba"})
                    last_interaction_time = time.time()

        try:
            if hasattr(face, "update"):
                face.update()
        except Exception as e:

        try:
            if hasattr(face, "update_gaze"):
                face.update_gaze(*mouse_pos)
        except Exception as e:

        if now - last_interaction_time > 8:
            idle_look_timer += clock.get_time() / 1000.0
            if idle_look_timer > 2.0:
                idle_look_timer = 0.0
                try:
                    if hasattr(face, "set_state"):
                        face.set_state("idle")
                except Exception as e:

        try:
            if hasattr(face, "draw"):
                face.draw(screen)
        except Exception as e:

        pygame.display.flip()
        clock.tick(30)

    try:
        speech.stop_auto_listener()
    except Exception as e:

    pygame.quit()


if __name__ == "__main__":
    main()
