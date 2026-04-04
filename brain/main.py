import pygame
import threading
from face_ui import PoodleFace
from speech_engine import PoodleSpeech

def main():
    # Pygame Başlatma
    pygame.init()
    screen = pygame.display.set_mode((1024, 600))
    pygame.display.set_caption("Poodle Robot - Voice & Vision")
    clock = pygame.time.Clock()

    # Modülleri Yükle
    face = PoodleFace(1024, 600)
    speech = PoodleSpeech()
    
    follow_mouse = True
    running = True

    print("\n--- Poodle Robot Aktif ---")
    print("M: Kamera/Mouse takibi arası geçiş")
    print("L: DINLEME MODU (Tanem ile konuş)")
    print("SPACE: KONUŞMA TESTİ")
    print("I: Boşta (Idle) modu")
    print("Q: Çıkış")

    def voice_interaction():
        """Arayüzü dondurmamak için ses işlemlerini ayrı bir kanalda çalıştırır."""
        # 1. Dinleme
        face.set_state("listening")
        user_text = speech.listen()
        
        if user_text:
            # 2. Cevap Verme (Burada basit bir tekrar yapıyoruz, ileride zeka eklenecek)
            face.set_state("speaking")
            speech.speak(f"Anladım Tanem, şöyle dedin: {user_text}")
        else:
            face.set_state("error")
            speech.speak("Üzgünüm, seni tam duyamadım.")
            
        # 3. Normale Dönüş
        face.set_state("idle")

    while running:
        mouse_x, mouse_y = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_m:
                    follow_mouse = not follow_mouse
                    print(f"Takip Modu: {'Aktif' if follow_mouse else 'Kapalı'}")
                
                elif event.key == pygame.K_l:
                    # Ses etkileşimini ayrı bir thread'de başlat ki ekran donmasın
                    threading.Thread(target=voice_interaction, daemon=True).start()
                
                elif event.key == pygame.K_SPACE:
                    face.set_state("speaking")
                    threading.Thread(target=lambda: speech.speak("Merhaba Tanem, ben Poodle!"), daemon=True).start()
                
                elif event.key == pygame.K_i:
                    face.set_state("idle")
                
                elif event.key == pygame.K_q:
                    running = False

        # Görsel Güncelleme
        if follow_mouse:
            face.update_gaze(mouse_x, mouse_y)
        else:
            face.update_gaze(None, None)

        face.draw(screen)
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    main()
