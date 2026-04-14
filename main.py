import time
import pygame

from brain import PoodleBrain
from speech import PoodleSpeech
from speech.pipeline import AudioPipeline
from character_ui import PoodleCharacter


def boot_log(msg: str):
    print(f"[BOOT] {msg}", flush=True)


def main():
    boot_log("main() entered")
    pygame.init()
    boot_log("pygame.init done")

    screen = pygame.display.set_mode((1024, 600))
    boot_log("display created")

    pygame.display.set_caption("Poodle Robot - AI Brain")
    clock = pygame.time.Clock()
    boot_log("clock created")

    boot_log("creating face...")
    face = PoodleCharacter(1024, 600)
    boot_log("face created")

    boot_log("creating brain...")
    brain = PoodleBrain()
    boot_log("brain created")

    boot_log("creating speech...")
    speech = PoodleSpeech()
    boot_log("speech created")

    boot_log("creating pipeline...")
    pipeline = AudioPipeline(speech=speech, brain=brain, face=face)
    boot_log("pipeline created")

    boot_log("debug mic list...")
    speech.debug_list_input_devices()
    boot_log("debug mic list done")

    boot_log("select mic...")
    speech.select_default_input_device()
    boot_log("select mic done")

    boot_log("start listener...")
    speech.start_auto_listener()
    boot_log("listener start called")

    print("\n--- Poodle Robot Aktif ---", flush=True)

    running = True
    last_interaction_time = time.time()
    idle_look_timer = 0.0

    while running:
        now = time.time()
        mouse_pos = pygame.mouse.get_pos()

        event = speech.get_pending_event()
        if event["type"] != "none":
            boot_log(f"event received: {event['type']}")
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
            print(f"[BOOT] face.update error: {type(e).__name__}: {e}", flush=True)

        try:
            if hasattr(face, "update_gaze"):
                face.update_gaze(*mouse_pos)
        except Exception as e:
            print(f"[BOOT] face.update_gaze error: {type(e).__name__}: {e}", flush=True)

        if now - last_interaction_time > 8:
            idle_look_timer += clock.get_time() / 1000.0
            if idle_look_timer > 2.0:
                idle_look_timer = 0.0
                try:
                    if hasattr(face, "set_state"):
                        face.set_state("idle")
                except Exception as e:
                    print(f"[BOOT] face.set_state error: {type(e).__name__}: {e}", flush=True)

        try:
            if hasattr(face, "draw"):
                face.draw(screen)
        except Exception as e:
            print(f"[BOOT] face.draw error: {type(e).__name__}: {e}", flush=True)

        pygame.display.flip()
        clock.tick(30)

    try:
        speech.stop_auto_listener()
    except Exception as e:
        print(f"[BOOT] stop listener error: {type(e).__name__}: {e}", flush=True)

    pygame.quit()


if __name__ == "__main__":
    main()
