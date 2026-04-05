import pygame
import threading
import random
import time
from face_ui import PoodleFace
from speech_engine import PoodleSpeech
from brain import PoodleBrain  # Yeni Beyin Modülü

# Beyni global veya main içinde tanımlayabiliriz
brain = PoodleBrain()

def main():
    pygame.init()
    screen = pygame.display.set_mode((1024, 600))
    pygame.display.set_caption("Poodle Robot - Llama-3 Brain")
    clock = pygame.time.Clock()

    face = PoodleFace(1024, 600)
    speech = PoodleSpeech()
    
    running = True
    is_busy = False 
    last_interaction_time = time.time()
    idle_look_timer = 0

    # --- SESLİ ETKİLEŞİM FONKSİYONU (main içinde olmalı ki nonlocal çalışsın) ---
    def voice_interaction():
        nonlocal last_interaction_time, is_busy
        is_busy = True
        
        face.set_state("listening")
        user_text = speech.listen()
        
        if user_text:
            face.set_state("speaking")
            # --- LLM + HAFIZA DEVREDE ---
            poodle_response = brain.ask_poodle(user_text)
            speech.speak(poodle_response)
        else:
            face.set_state("error")
            speech.speak("Seni tam duyamadım Tanem, tekrar söyler misin?")
        
        face.set_state("idle")
        last_interaction_time = time.time()
        is_busy = False

    print("\n--- Poodle Robot Zeka Katmanıyla Aktif ---")

    while running:
        now = time.time()
        mouse_pos = pygame.mouse.get_pos()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and not is_busy:
                if event.key == pygame.K_l:
                    threading.Thread(target=voice_interaction, daemon=True).start()
                elif event.key == pygame.K_SPACE:
                    face.set_state("speaking")
                    # Kısa bir selamlama için de LLM kullanabiliriz:
                    threading.Thread(target=lambda: speech.speak(brain.ask_poodle("Merhaba")), daemon=True).start()
                elif event.key == pygame.K_q:
                    running = False

        # --- OTONOM DAVRANIŞLAR ---
        if not is_busy:
            if now - last_interaction_time > 10:
                if now > idle_look_timer:
                    rx, ry = random.randint(200, 800), random.randint(150, 450)
                    face.update_gaze(rx, ry)
                    idle_look_timer = now + random.uniform(3, 6)
            else:
                face.update_gaze(mouse_pos[0], mouse_pos[1])

        face.draw(screen)
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    main()
