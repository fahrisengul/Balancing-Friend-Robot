import pygame
from vision import RobotVision
from face_ui import PoodleFace

def main():
    # 1. Başlatmalar
    pygame.init()
    screen = pygame.display.set_mode((1024, 600))
    pygame.display.set_caption("Poodle Robot Simülasyonu")
    clock = pygame.time.Clock()
    
    vision = RobotVision()
    face = PoodleFace()

    print("Sanal Beyin Çalışıyor... Çıkmak için 'Q'ya basın.")

    running = True
    while running:
        # 2. Girdi: Kameradan koordinatları al
        tx, ty = vision.get_target_coordinates()
        
        if tx == "EXIT": break

        # 3. İşlem: Koordinatları yüze aktar
        face.update_gaze(tx, ty)

        # 4. Çıktı: Ekranı çiz
        face.draw(screen)
        
        pygame.display.flip()
        
        # Olay Kontrolü
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        clock.tick(30) # 30 FPS simülasyon hızı

    vision.close()
    pygame.quit()

if __name__ == "__main__":
    main()
