import pygame
from vision import RobotVision
from face_ui import PoodleFace

def main():
    # 1. Başlatmalar
    pygame.init()
    # Poodle ekran boyutuna göre pencereyi ayarla
    screen = pygame.display.set_mode((1024, 600))
    pygame.display.set_caption("Poodle Robot - Sanal Beyin Simülasyonu")
    clock = pygame.time.Clock()
    
    # Modülleri yükle
    vision = RobotVision()
    face = PoodleFace(1024, 600)

    print("--- Poodle Robot Aktif ---")
    print("M: Kamera/Mouse takibi arası geçiş")
    print("SPACE: Konuşma modunu test et")
    print("L: Dinleme moduna geç")
    print("I: Boşta (Idle) moduna geç")
    print("Q: Çıkış")

    running = True
    follow_camera = True # Varsayılan olarak kamera takibi açık

    while running:
        # 2. Girdi: Kameradan koordinatları al
        tx, ty = vision.get_target_coordinates()
        
        # 'Q' tuşuna basılırsa veya pencere kapatılırsa çık
        if tx == "EXIT": 
            break

        # 3. Olay (Event) Kontrolü
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_m:
                    follow_camera = not follow_camera
                    mode = "KAMERA" if follow_camera else "MOUSE"
                    print(f"Takip Modu Değişti: {mode}")
                
                # ChatGPT'nin eklediği durumları test etmek için kısayollar
                elif event.key == pygame.K_SPACE:
                    new_state = "idle" if face.state == "speaking" else "speaking"
                    face.set_state(new_state)
                elif event.key == pygame.K_l:
                    face.set_state("listening")
                elif event.key == pygame.K_i:
                    face.set_state("idle")
                elif event.key == pygame.K_q:
                    running = False

        # 4. Mantık: Takip ve Durum Yönetimi
        if follow_camera:
            if tx is not None:
                face.update_gaze(tx, ty)
                # Birini gördüğünde eğer konuşmuyorsa otomatik 'listening' moduna geçebilir
                if face.state == "idle":
                    face.set_state("listening")
            else:
                face.update_gaze(None, None)
                if face.state == "listening":
                    face.set_state("idle")
        else:
            # Mouse ile takip modu (Manuel test için)
            mx, my = pygame.mouse.get_pos()
            face.update_gaze(mx, my)
            
        # 5. Çıktı: Ekranı çiz
        face.draw(screen)
        pygame.display.flip()
        
        # 30-60 FPS arası akıcılık
        clock.tick(30)

    # Kapanış işlemleri
    vision.close()
    pygame.quit()

if __name__ == "__main__":
    main()
