import pygame
import random

class PoodleFace:
    def __init__(self, width=1024, height=600):
        self.width = width
        self.height = height
        
        # --- RENK PALETİ (Dostane ve Robotik) ---
        self.COLOR_BG = (10, 10, 10)       # Derin Siyah (Ekran yokmuş gibi durması için)
        self.COLOR_FUR = (240, 230, 210)    # Krem/Kirli Beyaz (Poodle tüyleri)
        self.COLOR_EYE_OUT = (30, 30, 30)  # Göz Çevresi (Koyu Gri)
        self.COLOR_PUPIL = (0, 0, 0)       # Göz Bebeği (Tam Siyah)
        self.COLOR_NOSE = (20, 20, 20)      # Burun (Çok Koyu Gri)
        self.COLOR_GLINT = (255, 255, 255)  # Parlama (Işık Yansıması)

        # --- GEOMETRİK MERKEZLER ---
        self.center_x = width // 2
        self.center_y = height // 2
        
        # Gözlerin ve Kulakların Pozisyonları (Ana Merkeze Göre)
        self.eye_offset_x = 160
        self.eye_offset_y = -30
        self.ear_offset_x = 320
        self.nose_offset_y = 100

        # Göz Hareket Sınırları
        self.pupil_offset = [0, 0]
        
        # Göz Kırpma Ayarları
        self.is_blinking = False
        self.last_blink = pygame.time.get_ticks()
        self.next_blink_time = random.randint(3000, 7000)

    def update_gaze(self, target_x, target_y):
        """Kameradan gelen koordinatları göz hareketine çevirir."""
        if target_x is None:
            self.pupil_offset = [0, 0] # Kimse yoksa merkeze bak
            return

        # Kameradaki merkeze uzaklığı hesapla (Normalize et)
        dx = (target_x - 320) / 10
        dy = (target_y - 240) / 10
        
        # Gözlerin dışarı çıkmaması için hareket sınırı (Mühendislik limiti)
        self.pupil_offset[0] = max(-35, min(35, dx))
        self.pupil_offset[1] = max(-20, min(20, dy))

    def _draw_curly_ear(self, screen, x, y):
        """Poodle'ın kıvırcık kulağını stilize dairelerle çizer."""
        for i in range(5):
            angle = i * 20
            # Kulak şeklini oluşturan tüyler
            curr_x = x + (i * 10) * (-1 if x < self.center_x else 1)
            curr_y = y + (i * 15)
            pygame.draw.circle(screen, self.COLOR_FUR, (curr_x, curr_y), 45 - (i*3))

    def draw(self, screen):
        # 1. Arka Planı Temizle
        screen.fill(self.COLOR_BG)

        # 2. Kulakları Çiz (Stilize ve Kıvırcık)
        self._draw_curly_ear(screen, self.center_x - self.ear_offset_x, self.center_y - 80)
        self._draw_curly_ear(screen, self.center_x + self.ear_offset_x, self.center_y - 80)

        # 3. Yüzün Ana Hattı (Büyük krem daire)
        pygame.draw.circle(screen, self.COLOR_FUR, (self.center_x, self.center_y), 260)

        # 4. Göz Kırpma Zamanlaması
        now = pygame.time.get_ticks()
        if now - self.last_blink > self.next_blink_time:
            self.is_blinking = True
            if now - self.last_blink > self.next_blink_time + 120: # 120ms kapalı
                self.is_blinking = False
                self.last_blink = now
                self.next_blink_time = random.randint(3000, 9000)

        # 5. Gözleri Çiz
        for side in [-1, 1]: # -1 Sol, 1 Sağ
            # Gözün ana pozisyonu
            eye_x = self.center_x + (self.eye_offset_x * side)
            eye_y = self.center_y + self.eye_offset_y
            
            # Göz Çevresi (Dış halka)
            pygame.draw.circle(screen, self.COLOR_EYE_OUT, (eye_x, eye_y), 85)

            if self.is_blinking:
                # Göz kapalıyken: Yatay bir çizgi (Minimalist kapak)
                pygame.draw.line(screen, self.COLOR_PUPIL, 
                                 (eye_x - 60, eye_y), (eye_x + 60, eye_y), 10)
            else:
                # Göz Bebeği (Hareketli Kısım)
                pupil_x = eye_x + self.pupil_offset[0]
                pupil_y = eye_y + self.pupil_offset[1]
                pygame.draw.circle(screen, self.COLOR_PUPIL, (pupil_x, pupil_y), 50)
                
                # Işık parlaması (Canlılık verir)
                pygame.draw.circle(screen, self.COLOR_GLINT, 
                                   (pupil_x - 15, pupil_y - 15), 15)

        # 6. Burun (Stilize Poodle burnu)
        pygame.draw.ellipse(screen, self.COLOR_NOSE, 
                           (self.center_x - 50, self.center_y + self.nose_offset_y, 100, 60))
        # Burun parlaması
        pygame.draw.ellipse(screen, (40, 40, 40), 
                           (self.center_x - 30, self.center_y + self.nose_offset_y + 10, 40, 20))
