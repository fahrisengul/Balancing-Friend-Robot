import pygame
import sys
from vision import RobotVision
from face_ui import PoodleFace

def main():
    # 1. Başlatmalar
    pygame.init()
    
    # Ekran boyutunu Poodle görseline göre 1024x600 yapıyoruz
    width, height = 1024, 600
    screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption("Poodle Robot - Tanem Eğitim Koçu Simülasyonu")
    clock = pygame.time.Clock()
    
    # Modülleri yükle
    vision = RobotVision()
    face = PoodleFace(width, height)

    print("\n--- Poodle Robot Aktif ---")
    print("M: Kamera/Mouse takibi arası geçiş")
    print("SPACE: Konuşma modunu test et")
    print("L: Dinleme moduna geç")
    print("I: Boşta (Idle) moduna geç")
    print("OK TUSLARI: Gözleri milimetrik kalibre et")
    print("Q: Çıkış\n")

    running = True
    follow_camera = True # Varsayılan olarak kamera takibi açık

    while running:
        # 2. Girdi: Kameradan koordinatları al
        tx, ty = vision.get_target_coordinates()
        
        # 'EXIT' sinyali gelirse döngüden çık
        if tx == "EXIT": 
            break

        # 3. Olay (Event) Kontrolü
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            if event.type == pygame.KEYDOWN:
                # --- KALİBRASYON TETİKLEYİCİ ---
                # Ok tuşlarına basıldığında face_ui içindeki kaydırma fonksiyonunu çağırır
                if event.key in [pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT]:
                    face.handle_calibration(event.key)

                # Takip Modu Değiştirme
                if event.key == pygame.K_m:
                    follow_camera = not follow_camera
                    mode = "KAMERA" if follow_camera else "MOUSE"
                    print(f"Takip Modu Değişti: {mode}")
                
                # Durum (State) Testleri
                elif event.key == pygame.K_SPACE:
                    new_state = "idle" if face.state == "speaking" else "speaking"
                    face.set_state(new_state)
                    print(f"Durum Değişti: {face.state}")
                elif event.key == pygame.K_l:
                    face.set_state("listening")
                    print("Durum Değişti: Listening")
                elif event.key == pygame.K_i:
                    face.set_state("idle")
                    print("Durum Değişti: Idle")
                elif event.key == pygame.K_q:
                    running = False

        # 4. Mantık: Takip Yönetimi
        if follow_camera:
            if tx is not None:
                face.update_gaze(tx, ty)
            else:
                face.update_gaze(None, None)
        else:
            # Mouse ile takip modu
            mx, my = pygame.mouse.get_pos()
            face.update_gaze(mx, my)

        # 5. Çıktı: Ekranı çiz
        # face.draw fonksiyonu face_ui.py içindeki çizim mantığını çalıştırır
        face.draw(screen)
        pygame.display.flip()
        
        # Akıcılık için 30 FPS
        clock.tick(30)

    # Kapanış
    vision.close()
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
