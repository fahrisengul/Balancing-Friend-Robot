import pygame
import random

class PoodleFace:
    def __init__(self, width=1024, height=600):
        self.width = width
        self.height = height
        # Göz ve Burun Merkezleri
        self.left_eye_center = [width // 2 - 180, height // 2 - 50]
        self.right_eye_center = [width // 2 + 180, height // 2 - 50]
        self.nose_pos = [width // 2, height // 2 + 80]
        
        # Göz Bebeklerinin Mevcut Konumu (Takip için)
        self.pupil_offset = [0, 0]
        
        # Göz Kırpma Ayarları
        self.is_blinking = False
        self.last_blink = pygame.time.get_ticks()

    def update_gaze(self, target_x, target_y):
        """Kameradan gelen koordinatlara göre göz bebeklerini hareket ettirir."""
        if target_x is None:
            # Kimse yoksa ortaya bak
            self.pupil_offset = [0, 0]
            return

        # Koordinatları normalize et (-30 ile 30 piksel arası hareket sınırı)
        # Kamera genişliği genelde 640x480'dir, ona göre oranlıyoruz
        dx = (target_x - 320) / 10
        dy = (target_y - 240) / 10
        
        # Hareket sınırlandırması (Gözlerin dışarı çıkmaması için)
        self.pupil_offset[0] = max(-40, min(40, dx))
        self.pupil_offset[1] = max(-20, min(20, dy))

    def draw(self, screen):
        screen.fill((10, 10, 10)) # Siyah Arka Plan

        # Göz Kırpma Kontrolü
        now = pygame.time.get_ticks()
        if now - self.last_blink > random.randint(3000, 7000):
            self.is_blinking = True
            if now - self.last_blink > 3200: # 200ms kapalı kalsın
                self.is_blinking = False
                self.last_blink = now

        # Gözleri Çiz
        for center in [self.left_eye_center, self.right_eye_center]:
            if self.is_blinking:
                # Göz kapalıyken çizgi çek
                pygame.draw.line(screen, (40, 40, 40), (center[0]-60, center[1]), (center[0]+60, center[1]), 5)
            else:
                # Göz Akı (Siyah Poodle Gözü)
                pygame.draw.circle(screen, (20, 20, 20), center, 70)
                # Göz Bebeği (Takip Eden Kısım)
                pupil_pos = (center[0] + self.pupil_offset[0], center[1] + self.pupil_offset[1])
                pygame.draw.circle(screen, (0, 0, 0), pupil_pos, 40)
                # Parlama (Canlılık veren beyaz nokta)
                pygame.draw.circle(screen, (255, 255, 255), (pupil_pos[0]-15, pupil_pos[1]-15), 10)

        # Burun
        pygame.draw.ellipse(screen, (20, 20, 20), (self.nose_pos[0]-40, self.nose_pos[1]-25, 80, 50))
