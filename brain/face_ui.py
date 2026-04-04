import pygame
import random
import os
import math

class PoodleFace:
    def __init__(self, width=1024, height=600):
        self.width = width
        self.height = height

        current_dir = os.path.dirname(os.path.abspath(__file__))
        bg_path = os.path.join(current_dir, "poddle_v3.png")

        try:
            self.bg_image = pygame.image.load(bg_path).convert()
            self.bg_image = pygame.transform.scale(self.bg_image, (self.width, self.height))
            self.has_bg = True
            print(">>> [V11 - DARALTILMIS SIYAH GOZLER] AKTIF <<<")
        except Exception as e:
            self.has_bg = False
            self.bg_image = None
            print(f"Arka plan yuklenemedi: {e}")

        # --- RIG AYARLARI (DARALTILMIS) ---
        self.EYE_WIDTH = 70   # Genişlik daraltıldı (Eski: 94)
        self.EYE_HEIGHT = 140 # Yükseklik daraltıldı (Eski: 190)
        self.EYE_Y_LEVEL = 285 # Gözlerin dikey hizası
        self.EYE_SPACING = 328 # İki göz arası mesafe (348 ve 675 merkezleri için)
        
        self.EYE_COLOR = (15, 15, 15) # Derin Siyah
        self.PUPIL_COLOR = (255, 255, 255) # Parlama

        # --- DURUM VE ANIMASYON ---
        self.eye_pos = [0, 0]
        self.target_pos = [0, 0]
        self.eye_scale_y = 1.0
        self.target_scale_y = 1.0
        self.state = "idle"
        self.last_blink = pygame.time.get_ticks()

    def set_state(self, state):
        self.state = state
        if state == "listening":
            self.target_scale_y = 1.25
        elif state == "speaking":
            self.target_scale_y = 0.90
        else:
            self.target_scale_y = 1.0

    def update_gaze(self, tx, ty):
        if tx is not None and ty is not None:
            # Gözlerin yuvadan taşmaması için hareket alanını iyice daralttık
            self.target_pos = [(tx - self.width//2) / 100, (ty - self.height//2) / 100]
        else:
            self.target_pos = [0, 0]

    def draw(self, screen):
        if self.has_bg:
            screen.blit(self.bg_image, (0, 0))
        else:
            screen.fill((10, 10, 15))

        # Pürüzsüzleştirme (LERP)
        self.eye_pos[0] += (self.target_pos[0] - self.eye_pos[0]) * 0.1
        self.eye_pos[1] += (self.target_pos[1] - self.eye_pos[1]) * 0.1
        self.eye_scale_y += (self.target_scale_y - self.eye_scale_y) * 0.1

        # Göz Kırpma
        now = pygame.time.get_ticks()
        if now - self.last_blink > random.randint(3000, 8000):
            self.eye_scale_y = 0.05
            if now - self.last_blink > 3150:
                self.last_blink = now

        # Merkez Koordinatları Hesapla
        l_center = (self.width // 2 - self.EYE_SPACING // 2, self.EYE_Y_LEVEL)
        r_center = (self.width // 2 + self.EYE_SPACING // 2, self.EYE_Y_LEVEL)
        
        curr_w = self.EYE_WIDTH
        curr_h = self.EYE_HEIGHT * self.eye_scale_y

        for base_x, base_y in [l_center, r_center]:
            x = base_x + self.eye_pos[0]
            y = base_y + self.eye_pos[1]

            # 1. Ana Göz (Siyah)
            pygame.draw.ellipse(screen, self.EYE_COLOR, 
                                (x - curr_w//2, y - curr_h//2, curr_w, curr_h))
            
            # 2. Parlama (Beyaz)
            if self.eye_scale_y > 0.4:
                pygame.draw.ellipse(screen, self.PUPIL_COLOR, 
                                    (x - 8, y - curr_h//3, 16, 12))

    # main.py ile uyumluluk için boş fonksiyon
    def handle_calibration(self, key):
        pass
