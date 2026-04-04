import pygame
import random

class PoodleFace:
    def __init__(self, width=1024, height=600):
        self.width = width
        self.height = height
        
        # --- MÜKEMMELLEŞTİRİLMİŞ RENK PALETİ ---
        self.COLOR_BG = (10, 10, 10)       # Derin Siyah arka plan
        self.COLOR_FUR = (245, 235, 215)    # Krem/Kirli Beyaz Poodle tüyleri (Biraz daha sıcak)
        self.COLOR_EYE_OUT = (25, 25, 25)   # Göz Çevresi (Panda etkisini azaltmak için koyu gri)
        self.COLOR_PUPIL = (0, 0, 0)       # Göz Bebeği (Tam Siyah)
        self.COLOR_NOSE = (20, 20, 20)      # Burun
        self.COLOR_GLINT = (255, 255, 255)  # Canlı Parlama (Daha büyük ve belirgin)

        # --- YENİ GEOMETRİK MERKEZLER (Taşmayı Önlemek İçin) ---
        self.center_x = width // 2
        self.center_y = height // 2 - 20 # Kafayı biraz yukarı çektik
        
        # Göz ve Kulak Pozisyonları
        self.eye_offset_x = 150 # Gözleri biraz birbirine yaklaştırdık (Daha dostane)
        self.eye_offset_y = -40
        self.ear_offset_x = 310 # Kulakları kafaya yaklaştırdık
        self.nose_offset_y = 90  # Burnu yukarı çektik (Taşmayı önlemek için)

        # Göz Hareket Sınırları
        self.pupil_offset = [0, 0]
        
        # Göz Kırpma Ayarları
        self.is_blinking = False
        self.last_blink = pygame.time.get_ticks()
        self.next_blink_time = random.randint(3000, 7000)

    def update_gaze(self, target_x, target_y):
        """Kameradan gelen koordinatları göz hareketine çevirir."""
        if target_x is None:
            self.pupil_offset = [0, 0]
            return

        # Normalize et (Hareket sınırlandırması daha hassas)
        dx = (target_x - 320) / 12
        dy = (target_y - 240) / 12
        
        self.pupil_offset[0] = max(-30, min(30, dx))
        self.pupil_offset[1] = max(-15, min(15, dy))

    def _draw_fluffy_ear(self, screen, x, y):
        """Kıvırcık Poodle kulağını tüy hissi veren dairelerle çizer."""
        # Üç daireyi üst üste bindirerek 'tüy demeti' hissi veriyoruz
        base_radius = 55
        for i in range(3):
            # Her daire bir öncekinden biraz daha aşağıda ve küçük
            curr_y = y + (i * 25)
            pygame.draw.circle(screen, self.COLOR_FUR, (x, curr_y), base_radius - (i*5))

    def _draw_main_face(self, screen):
        """Yüzün ana krem hattını ve tüy detaylarını çizer."""
        # Ana yüz dairesi (Artık taşmıyor)
        pygame.draw.circle(screen, self.COLOR_FUR, (self.center_x, self.center_y), 240)
        
        # Alın ve çene kısmına minimalist 'tüy kıvrımları' ekleyelim (Opsiyonel)
        for i in range(3):
            offset_y = 190 + (i*15)
            width = 120 - (i*20)
            pygame.draw.ellipse(screen, self.COLOR_FUR, 
                               (self.center_x - width//2, self.center_y - offset_y, width, 40))

    def draw(self, screen):
        # 1. Arka Planı Temizle
        screen.fill(self.COLOR_BG)

        # 2. Kulakları Çiz (Stilize ve Kıvırcık tüy demetleri)
        self._draw_fluffy_ear(screen, self.center_x - self.ear_offset_x, self.center_y - 80)
        self._draw_fluffy_ear(screen, self.center_x + self.ear_offset_x, self.center_y - 80)

        # 3. Yüzün Ana Krem Hattını Çiz
        self._draw_main_face(screen)

        # 4. Göz Kırpma Zamanlaması
        now = pygame.time.get_ticks()
        if now - self.last_blink > self.next_blink_time:
            self.is_blinking = True
            if now - self.last_blink > self.next_blink_time + 100: # 100ms hızlı kırpma
                self.is_blinking = False
                self.last_blink = now
                self.next_blink_time = random.randint(3000, 9000)

        # 5. Gözleri Çiz (Daha sevimli ve dostane)
        for side in [-1, 1]: # -1 Sol, 1 Sağ
            # Gözün ana pozisyonu
            eye_x = self.center_x + (self.eye_offset_x * side)
            eye_y = self.center_y + self.eye_offset_y
            
            # Göz Çevresi (Artık Panda gibi değil, minimalist koyu halka)
            pygame.draw.circle(screen, self.COLOR_EYE_OUT, (eye_x, eye_y), 75)

            if self.is_blinking:
                # Göz kapalıyken minimalist yatay kapak
                pygame.draw.line(screen, self.COLOR_PUPIL, 
                                 (eye_x - 50, eye_y), (eye_x + 50, eye_y), 8)
            else:
                # Göz Bebeği (Daha büyük ve canlı)
                pupil_x = eye_x + self.pupil_offset[0]
                pupil_y = eye_y + self.pupil_offset[1]
                pygame.draw.circle(screen, self.COLOR_PUPIL, (pupil_x, pupil_y), 45)
                
                # Mükemmel Parlama (Daha büyük ve belirgin)
                pygame.draw.circle(screen, self.COLOR_GLINT, 
                                   (pupil_x - 12, pupil_y - 12), 12)

        # 6. Burun (Stilize Poodle burnu - Taşmıyor)
        pygame.draw.ellipse(screen, self.COLOR_NOSE, 
                           (self.center_x - 45, self.center_y + self.nose_offset_y, 90, 55))
        # Burun parlaması
        pygame.draw.ellipse(screen, (40, 40, 40), 
                           (self.center_x - 25, self.center_y + self.nose_offset_y + 10, 35, 18))
