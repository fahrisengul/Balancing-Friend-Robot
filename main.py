import sys
import time
import random
import threading
import traceback
import pygame

from brain import PoodleBrain
from speech import PoodleSpeech
from speech.pipeline import AudioPipeline

try:
    from character_ui import PoodleFace
except Exception:
    try:
        from character_ui import PoodleCharacter as PoodleFace
    except Exception:
        from face_ui import PoodleFace


def boot(msg: str):
    print(f"[BOOT] {msg}")


def build_face(width: int, height: int):
    boot("build_face() entered")
    try:
        face = PoodleFace(width, height)
        boot("face created with width/height")
        return face
    except TypeError:
        try:
            face = PoodleFace()
            boot("face created with empty ctor")
            return face
        except Exception as e:
            boot(f"face creation failed: {type(e).__name__}: {e}")
            traceback.print_exc()
            return None
    except Exception as e:
        boot(f"face creation failed: {type(e).__name__}: {e}")
        traceback.print_exc()
        return None


def main():
    boot("main() entered")

    pygame.init()
    boot("pygame.init done")

    screen = pygame.display.set_mode((1024, 600))
    boot("display created")

    pygame.display.set_caption("Poodle Robot - AI Brain")
    clock = pygame.time.Clock()
    boot("clock created")

    face = build_face(1024, 600)

    boot("creating brain...")
    brain = PoodleBrain()
    boot("brain created")

    boot("creating speech...")
    speech = PoodleSpeech(input_device_index=0)
    boot("speech created")

    boot("creating pipeline...")
    pipeline = AudioPipeline(speech=speech, brain=brain, face=face)
    boot("pipeline created")

    running = True
    last_interaction_time = time.time()
    idle_look_timer = 0

    boot("starting auto listener...")
    speech.start_auto_listener()
    boot("auto listener started")

    print("\n--- Poodle Robot Aktif ---")

    try:
        loop_count = 0

        while running:
            loop_count += 1
            now = time.time()

            # DEBUG: loop yaşıyor mu?
            if loop_count % 300 == 0:
                boot(f"main loop alive, count={loop_count}")

            try:
                evt = speech.get_pending_event()
                if evt.get("type") != "none":
                    boot(f"event received: {evt}")
                    pipeline.process_event(evt)
                    last_interaction_time = now
            except Exception as e:
                boot(f"event handling error: {type(e).__name__}: {e}")
                traceback.print_exc()

            try:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        boot("pygame.QUIT received")
                        running = False

                    elif event.type == pygame.KEYDOWN:
                        boot(f"KEYDOWN received: {event.key}")

                        if event.key == pygame.K_q:
                            boot("Q pressed -> exiting")
                            running = False

                        elif event.key == pygame.K_SPACE:
                            boot("SPACE pressed -> test command thread")
                            threading.Thread(
                                target=lambda: pipeline._handle_command("Merhaba"),
                                daemon=True,
                            ).start()
            except Exception as e:
                boot(f"pygame event loop error: {type(e).__name__}: {e}")
                traceback.print_exc()
                running = False

            try:
                if face is not None:
                    if now - last_interaction_time > 10:
                        if now > idle_look_timer:
                            rx = random.randint(200, 800)
                            ry = random.randint(150, 450)
                            if hasattr(face, "update_gaze"):
                                face.update_gaze(rx, ry)
                            idle_look_timer = now + random.uniform(3, 6)
                    else:
                        mx, my = pygame.mouse.get_pos()
                        if hasattr(face, "update_gaze"):
                            face.update_gaze(mx, my)

                    if hasattr(face, "draw"):
                        face.draw(screen)
            except Exception as e:
                boot(f"face draw/update error: {type(e).__name__}: {e}")
                traceback.print_exc()
                running = False

            try:
                pygame.display.flip()
                clock.tick(30)
            except Exception as e:
                boot(f"display/clock error: {type(e).__name__}: {e}")
                traceback.print_exc()
                running = False

    except Exception as e:
        boot(f"main() outer exception: {type(e).__name__}: {e}")
        traceback.print_exc()

    finally:
        boot("main() finally entered")
        try:
            speech.stop_auto_listener()
        except Exception as e:
            boot(f"stop_auto_listener error: {type(e).__name__}: {e}")
            traceback.print_exc()

        try:
            pygame.quit()
            boot("pygame.quit done")
        except Exception as e:
            boot(f"pygame.quit error: {type(e).__name__}: {e}")
            traceback.print_exc()

        boot("sys.exit about to run")
        sys.exit()


if __name__ == "__main__":
    main()
