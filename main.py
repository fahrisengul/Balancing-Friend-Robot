import sys
import time
import random
import threading
import pygame

from face_ui import PoodleFace
from speech_engine import PoodleSpeech
from brain import PoodleBrain
from brain.llm_client import LLMClient


def main():
    pygame.init()
    screen = pygame.display.set_mode((1024, 600))
    pygame.display.set_caption("Poodle Robot - AI Brain")
    clock = pygame.time.Clock()

    face = PoodleFace(1024, 600)

    llm = LLMClient()
    llm.warmup()
    brain = PoodleBrain(llm)

    speech = PoodleSpeech(input_device_index=None)
    speech.debug_list_input_devices()
    speech.select_default_input_device()

    running = True
    is_busy = False
    last_interaction_time = time.time()
    idle_look_timer = 0.0

    speech.start_auto_listener()

    def set_robot_busy(value: bool):
        nonlocal is_busy
        is_busy = value
        speech.set_busy(value)

    def run_response(user_text: str):
        nonlocal last_interaction_time

        if not user_text:
            return

        ignored_inputs = {"hey", "poodle", "tamam", "peki", "evet"}
        if user_text.strip().lower() in ignored_inputs:
            return

        set_robot_busy(True)

        try:
            face.set_state("thinking")

            if hasattr(brain, "handle_user_input"):
                result = brain.handle_user_input(user_text)
                poodle_response = result.reply_text if hasattr(result, "reply_text") else str(result)
            elif hasattr(brain, "handle"):
                result = brain.handle(user_text)
                poodle_response = result.reply_text if hasattr(result, "reply_text") else str(result)
            elif hasattr(brain, "ask_poodle"):
                poodle_response = brain.ask_poodle(user_text)
            else:
                raise RuntimeError("Brain tarafında kullanılabilir bir cevap metodu bulunamadı.")

            face.set_state("speaking")
            speech.speak(poodle_response)
            speech.flush_pending_tts()

        except Exception as e:
            print(f">>> [MAIN ERROR] {type(e).__name__}: {e}")
            face.set_state("error")
            speech.speak("Bir sorun yaşadım Tanem.")
            speech.flush_pending_tts()

        finally:
            face.set_state("idle")
            last_interaction_time = time.time()
            set_robot_busy(False)

    def manual_voice_interaction():
        nonlocal last_interaction_time

        if is_busy:
            return

        set_robot_busy(True)

        try:
            face.set_state("listening")
            user_text = speech.listen_command_vad()

            if user_text:
                face.set_state("thinking")

                if hasattr(brain, "handle_user_input"):
                    result = brain.handle_user_input(user_text)
                    poodle_response = result.reply_text if hasattr(result, "reply_text") else str(result)
                elif hasattr(brain, "handle"):
                    result = brain.handle(user_text)
                    poodle_response = result.reply_text if hasattr(result, "reply_text") else str(result)
                elif hasattr(brain, "ask_poodle"):
                    poodle_response = brain.ask_poodle(user_text)
                else:
                    raise RuntimeError("Brain tarafında kullanılabilir bir cevap metodu bulunamadı.")

                face.set_state("speaking")
                speech.speak(poodle_response)
                speech.flush_pending_tts()
            else:
                face.set_state("error")
                speech.speak("Seni tam duyamadım Tanem, tekrar söyler misin?")
                speech.flush_pending_tts()

        except Exception as e:
            print(f">>> [MAIN ERROR] {type(e).__name__}: {e}")
            face.set_state("error")
            speech.speak("Bir sorun yaşadım Tanem.")
            speech.flush_pending_tts()

        finally:
            face.set_state("idle")
            last_interaction_time = time.time()
            set_robot_busy(False)

    def quick_greeting():
        nonlocal last_interaction_time

        if is_busy:
            return

        set_robot_busy(True)

        try:
            face.set_state("speaking")

            if hasattr(brain, "handle_user_input"):
                result = brain.handle_user_input("Merhaba")
                greeting = result.reply_text if hasattr(result, "reply_text") else str(result)
            elif hasattr(brain, "handle"):
                result = brain.handle("Merhaba")
                greeting = result.reply_text if hasattr(result, "reply_text") else str(result)
            elif hasattr(brain, "ask_poodle"):
                greeting = brain.ask_poodle("Merhaba")
            else:
                greeting = "Selam!"

            speech.speak(greeting)
            speech.flush_pending_tts()

        finally:
            face.set_state("idle")
            last_interaction_time = time.time()
            set_robot_busy(False)

    print("\n--- Poodle Robot Aktif ---")
    print("Arka plan dinlemesi aktif.")
    print("L: Direkt Dinleme | SPACE: Selamla | Q: Çıkış")

    while running:
        now = time.time()

        if not is_busy:
            evt = speech.get_pending_event()

            if evt["type"] == "command":
                threading.Thread(
                    target=run_response,
                    args=(evt["text"],),
                    daemon=True,
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

            elif event.type == pygame.KEYDOWN and not is_busy:
                if event.key == pygame.K_l:
                    threading.Thread(target=manual_voice_interaction, daemon=True).start()

                elif event.key == pygame.K_SPACE:
                    threading.Thread(target=quick_greeting, daemon=True).start()

                elif event.key == pygame.K_q:
                    running = False

        if not is_busy:
            if now - last_interaction_time > 10:
                if now > idle_look_timer:
                    rx = random.randint(200, 800)
                    ry = random.randint(150, 450)
                    face.update_gaze(rx, ry)
                    idle_look_timer = now + random.uniform(3, 6)
            else:
                mx, my = pygame.mouse.get_pos()
                face.update_gaze(mx, my)

        face.draw(screen)
        pygame.display.flip()
        clock.tick(30)

    speech.stop_auto_listener()
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
