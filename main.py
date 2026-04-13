import pygame
import threading
import random
import time
import sys

from face_ui import PoodleFace
from speech_engine import PoodleSpeech
from brain import PoodleBrain
from brain.llm_client import LLMClient


def main():
    llm = LLMClient()
    if hasattr(llm, "warmup"):
        llm.warmup()
    brain = PoodleBrain(llm)

    pygame.init()
    screen = pygame.display.set_mode((1024, 600))
    pygame.display.set_caption("Poodle Robot - AI Brain")
    clock = pygame.time.Clock()

    face = PoodleFace(1024, 600)
    speech = PoodleSpeech()    
    speech.debug_list_input_devices()
    speech.select_default_input_device()

    running = True
    is_busy = False
    last_interaction_time = time.time()
    idle_look_timer = 0

    speech.start_auto_listener()

    def set_robot_busy(value: bool):
        nonlocal is_busy
        is_busy = value
        speech.set_busy(value)

    def get_brain_response(user_text: str) -> str:
        if hasattr(brain, "handle_user_input"):
            result = brain.handle_user_input(user_text)
            return result.reply_text if hasattr(result, "reply_text") else str(result)

        if hasattr(brain, "handle"):
            result = brain.handle(user_text)
            return result.reply_text if hasattr(result, "reply_text") else str(result)

        if hasattr(brain, "ask_poodle"):
            return brain.ask_poodle(user_text)

        raise RuntimeError("Brain tarafında kullanılabilir bir cevap metodu bulunamadı.")

    def run_response(user_text):
        nonlocal last_interaction_time

        if not user_text:
            return

        bad_inputs = {"hey", "poodle", "tamam", "peki", "evet"}
        if user_text.strip().lower() in bad_inputs:
            return

        set_robot_busy(True)

        try:
            face.set_state("thinking")
            poodle_response = get_brain_response(user_text)

            face.set_state("speaking")
            speech.speak(poodle_response)
            speech.flush_pending_tts()

        except Exception as e:
            print(f">>> [MAIN HATASI] {type(e).__name__}: {e}")
            face.set_state("error")
            speech.speak("Bir sorun yaşadım Tanem.")
            speech.flush_pending_tts()

        finally:
            face.set_state("idle")
            last_interaction_time = time.time()
            set_robot_busy(False)

    print("\n--- Poodle Robot Aktif ---")

    try:
        while running:
            now = time.time()

            if not is_busy:
                evt = speech.get_pending_event()

                if evt["type"] == "command":
                    threading.Thread(
                        target=run_response,
                        args=(evt["text"],),
                        daemon=True
                    ).start()

                elif evt["type"] == "sleep":
                    face.set_state("idle")

                elif evt["type"] == "resumed":
                    face.set_state("listening")

                elif evt["type"] == "clarify":
                    speech.speak(evt.get("text", "Seni tam anlayamadım."))
                    speech.flush_pending_tts()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            if not is_busy and hasattr(face, "update_gaze"):
                if now - last_interaction_time > 10:
                    if now > idle_look_timer:
                        face.update_gaze(random.randint(200, 800), random.randint(150, 450))
                        idle_look_timer = now + random.uniform(3, 6)
                else:
                    mx, my = pygame.mouse.get_pos()
                    face.update_gaze(mx, my)

            face.draw(screen)
            pygame.display.flip()
            clock.tick(30)

    finally:
        try:
            speech.stop_auto_listener()
        except Exception as e:
            print(f">>> [SHUTDOWN SPEECH ERROR] {type(e).__name__}: {e}")

        try:
            pygame.quit()
        except Exception as e:
            print(f">>> [SHUTDOWN PYGAME ERROR] {type(e).__name__}: {e}")

        sys.exit()


if __name__ == "__main__":
    main()
