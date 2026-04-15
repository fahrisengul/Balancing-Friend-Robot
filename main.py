import time
import random
import threading
import traceback
import pygame

from brain import PoodleBrain
from speech import PoodleSpeech

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
    speech = PoodleSpeech()
    boot("speech created")

    boot("starting auto listener...")
    speech.start_auto_listener(device_index=0)
    boot("auto listener started")

    print("\n--- Poodle Robot Aktif ---")

    running = True
    last_interaction_time = time.time()
    idle_look_timer = 0
    loop_count = 0

    try:
        while running:
            loop_count += 1
            now = time.time()

            if loop_count % 300 == 0:
                boot(f"main loop alive, count={loop_count}")

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
                        boot("SPACE pressed -> test speak")
                        threading.Thread(
                            target=lambda: speech.speak("Selam!"),
                            daemon=True,
                        ).start()

            if face is not None:
                try:
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
                    boot(f"face error: {type(e).__name__}: {e}")
                    traceback.print_exc()

            pygame.display.flip()
            clock.tick(30)

    except Exception as e:
        boot(f"main loop exception: {type(e).__name__}: {e}")
        traceback.print_exc()

    finally:
        boot("main() finally entered")
        try:
            speech.stop_auto_listener()
        except Exception as e:
            boot(f"stop_auto_listener error: {type(e).__name__}: {e}")
            traceback.print_exc()

        pygame.quit()
        boot("pygame.quit done")


if __name__ == "__main__":
    main()
