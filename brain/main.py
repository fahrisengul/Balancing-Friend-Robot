import pygame
import threading
import random
import time
import sys

from face_ui import PoodleFace
from speech_engine import PoodleSpeech
from brain import PoodleBrain

def main():
    pygame.init()
    screen = pygame.display.set_mode((1024, 600))
    pygame.display.set_caption("Poodle Robot - AI Brain")
    clock = pygame.time.Clock()

    face = PoodleFace(1024, 600)
    brain = PoodleBrain()
    
    # Varsayılan mikrofon için -1, listeden seçmek istersen ilgili indexi yaz
    speech = PoodleSpeech(input_device_index=-1)
    speech.debug_list_input_devices()

    running = True
    is_busy = False
    last_interaction_time = time.time()
    idle_look_timer = 0

    speech.start_auto_listener()

    def set_robot_busy(value: bool):
        nonlocal is_busy
        is_busy = value
        speech.set_busy(value)

    def run_response(user_text):
        nonlocal last_interaction_time
        if not user_text: return

        # Kısa ve anlamsız girişleri ele
        bad_inputs = {"hey", "poodle", "tamam", "peki", "evet"}
        if user_text.strip().lower() in bad_inputs: return

        set_robot_busy(True)
        try:
            face.set_state("listening")
            poodle_response = brain.ask_poodle(user_text)

            face.set_state("speaking")
            speech.speak(poodle_response)
        except Exception as e:
            print(f">>> [MAIN HATASI] {e}")
            face.set_state("error")
        finally:
            face.set_state("idle")
            last_interaction_time = time.time()
            set_robot_busy(False)

    print("\n--- Poodle Robot Aktif ---")

    while running:
        now = time.time()
        
        # Olayları ve Event Kuyruğunu İşle
        if not is_busy:
            evt = speech.get_pending_event()
            if evt["type"] == "command":
                threading.Thread(target=run_response, args=(evt["text"],), daemon=True).start()
            elif evt["type"] == "sleep":
                face.set_state("idle")
            elif evt["type"] == "resumed":
                face.set_state("listening")

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Görsel Güncelleme (Göz Hareketleri)
        if not is_busy:
            if now - last_interaction_time > 10:
                if now > idle_look_timer:
                    face.update_gaze(random.randint(200, 800), random.randint(150, 450))
                    idle_look_timer = now + random.uniform(3, 6)
            else:
                mx, my = pygame.mouse.get_pos()
                face.update_gaze(mx, my)

        face.draw(screen)
        pygame.display.flip()
        clock.tick(30) # CPU'yu yormamak için 30 FPS yeterli

    speech.stop_auto_listener()
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
