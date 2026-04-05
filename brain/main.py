import pygame
import threading
import random
import time
from face_ui import PoodleFace
from speech_engine import PoodleSpeech

def main():
    pygame.init()
    screen = pygame.display.set_mode((1024, 600))
    pygame.display.set_caption("Poodle Robot - Autonomous Character")
    clock = pygame.time.Clock()

    face = PoodleFace(1024, 600)
    speech = PoodleSpeech()
    
    follow_mouse = True
    running = True
    
    # --- OTONOM DAVRANIŞ DEĞİŞKENLERİ ---
    last_interaction_time = time.time()
    idle_look_timer = 0
    is_busy = False # Robot konuşurken veya dinlerken etkileşimi kilitlemek için

    print("\n--- Poodle Robot Canlandı ---")
    print("L: Dinleme Modu | SPACE: Selamla | Q: Çıkış")

    def voice_interaction():
        nonlocal last_interaction_time, is_busy
        is_busy = True
        
        face.set_state("listening")
        user_text = speech.listen()
        
        if user_text:
            face.set_state("speaking")
            # Basit bir zeka ekleyelim: Eğer 'merhaba' derse özel selam versin
            if "merhaba" in user_text:
                speech.speak("Merhaba Tanem! Bugün seninle oyun oynamak için sabırsızlanıyorum.")
            else:
                speech.speak(f"Anladım Tanem, şöyle dedin: {user_text}")
        
        face.set_state("idle")
        last_interaction_time = time.time()
        is_busy = False

    while running:
        now = time.time()
        mouse_pos = pygame.mouse.get_pos()
        
        # Etkileşim kontrolü (Mouse hareket ederse timer'ı sıfırla)
        if pygame.mouse.get_rel() != (0,0):
            last_interaction_time = now

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and not is_busy:
                if event.key == pygame.K_l:
                    threading.Thread(target=voice_interaction, daemon=True).start()
                elif event.key == pygame.K_SPACE:
                    last_interaction_time = now
                    face.set_state("speaking")
                    threading.Thread(target=lambda: speech.speak("Tanem, seni gördüğüme çok sevindim!"), daemon=True).start()
                elif event.key == pygame.K_q:
                    running = False

        # --- DAVRANIŞ AĞACI (BEHAVIOR LOGIC) ---
        if not is_busy:
            # Sıkılma Durumu: 10 saniye etkileşim olmazsa başlar
            if now - last_interaction_time > 10:
                if now > idle_look_timer:
                    # Rastgele bir yöne merakla bak
                    rx = random.randint(200, 800)
                    ry = random.randint(150, 450)
                    face.update_gaze(rx, ry)
                    # Bir sonraki hareket için rastgele bekleme (2-5 sn)
                    idle_look_timer = now + random.uniform(2, 5)
            else:
                # Normal Takip Modu
                face.update_gaze(mouse_pos[0], mouse_pos[1])

        face.draw(screen)
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    main()
