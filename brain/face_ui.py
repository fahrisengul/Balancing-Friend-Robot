import pygame
import random
import time

class PoodleFace:
    def __init__(self, width=1024, height=600):
        self.width = width
        self.height = height
        
        # --- 1. VARLIKLARI YÜKLE ---
        try:
            self.body_img = pygame.image.load("poodle_body.png").convert_alpha()
            self.pupil_img = pygame.image.load("poodle_pupil.png").convert_alpha()
            self.lid_img = pygame.image.load("poodle_lid.png").convert_alpha()
            self.mouth_img = pygame.image.load("poodle_mouth.png").convert_alpha()
        except pygame.error as e:
            print(f"Dosya yükleme hatası: {e}")
            exit()

        # --- 2. KOORDİNATLAR VE HİZALAMA ---
        # Resimlerinizin merkezini 1024x600 ekrana göre hizalıyoruz
        self.base_x = (width - self.body_img.get_width()) // 2
        self.base_y = (height - self.body_img.get_height()) // 2

        # Göz deliklerinin merkez koordinatları (Resimdeki yerlerine göre)
        self.left_eye_pos = (self.base_x + 405, self.base_y + 250)
        self.right_eye_pos = (self.base_x + 615, self.base_y + 250)
        
        # Hareket ve Animasyon Değişkenleri
        self.pupil_offset = [0.0, 0.0]
        self.target_offset = [0.0, 0.0]
        self.lerp_speed = 0.12 # Akıcı hareket hızı
        
        self.is_blinking = False
        self.blink_start = 0
        self.state = "idle" # idle, listening, speaking

    def set_state(self, state):
        self.state = state

    def update_gaze(self, target_x=None, target_y=None):
        if target_x is not None:
            # Kameradan gelen veriyi ofset değerine çevir
            self.target_offset[0] = max(-30, min(30, (target_x - 320) / 10))
            self.target_offset[1] = max(-15, min(15, (target_y - 240) / 10))
        else:
            # Kimse yoksa merkeze bak
            self.target_offset = [0, 0]

    def _animate(self):
        # Akıcı Göz Hareketi (LERP)
        self.pupil_offset[0] += (self.target_offset[0] - self.pupil_offset[0]) * self.lerp_speed
        self.pupil_offset[1] += (self.target_offset[1] - self.pupil_offset[1]) * self.lerp_speed

    def draw(self, screen):
        screen.fill((15, 15, 25)) # Koyu arka plan
        self._animate()
        
        # 1. KATMAN: GÖZ BEBEKLERİ (En arkada, deliklerin altında kalacak)
        for pos in [self.left_eye_pos, self.right_eye_pos]:
            p_rect = self.pupil_img.get_rect(center=pos)
            screen.blit(self.pupil_img, (p_rect.x + self.pupil_offset[0], p_rect.y + self.pupil_offset[1]))

        # 2. KATMAN: GÖVDE VE KAFA
        screen.blit(self.body_img, (self.base_x, self.base_y))

        # 3. KATMAN: KONUŞMA (Ağız)
        if self.state == "speaking":
            # Basit bir titreme efekti ile ağzı canlandırıyoruz
            m_offset = math.sin(time.time() * 15) * 5
            screen.blit(self.mouth_img, (self.base_x, self.base_y + m_offset))

        # 4. KATMAN: GÖZ KIRPMA (En üstte)
        now = pygame.time.get_ticks()
        if not self.is_blinking and random.random() < 0.01:
            self.is_blinking = True
            self.blink_start = now
        
        if self.is_blinking:
            screen.blit(self.lid_img, (self.base_x, self.base_y))
            if now - self.blink_start > 120:
                self.is_blinking = False
