import sys
import time
import random
import threading
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


def build_face(width: int, height: int):
    try:
        return PoodleFace(width, height)
    except TypeError:
        try:
            return PoodleFace()
        except Exception:
            return None


def main():
    pygame.init()
    screen = pygame.display.set_mode((1024, 600))
    pygame.display.set_caption("Poodle Robot - AI Brain")
    clock = pygame.time.Clock()

    face = build_face(1024, 600)
    brain = PoodleBrain()
    speech = PoodleSpeech(input_device_index=-1)
    pipeline = AudioPipeline(speech=speech, brain=brain, face=face)

    running = True
    last_interaction_time = time.time()
    idle_look_timer = 0

    speech.start_auto_listener()

    print("\n--- Poodle Robot Aktif ---")

    try:
        while running:
            now = time.time()

            event = speech.get_pending_event()
            if event.get("type") != "none":
                pipeline.process_event(event)
                last_interaction_time = now

            for pg_event in pygame.event.get():
                if pg_event.type == pygame.QUIT:
                    running = False

                elif pg_event.type == pygame.KEYDOWN:
                    if pg_event.key == pygame.K_q:
                        running = False

                    elif pg_event.key == pygame.K_SPACE:
                        threading.Thread(
                            target=lambda: pipeline._handle_command("Merhaba"),
                            daemon=True,
                        ).start()

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

            pygame.display.flip()
            clock.tick(30)

    finally:
        speech.stop_auto_listener()
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    main()
