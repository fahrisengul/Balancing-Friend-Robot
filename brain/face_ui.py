import pygame
import math
import random
import os

class PoodleFace:
    def __init__(self, width=1024, height=600):
        self.width = width
        self.height = height
        
        current_dir = os.path.dirname(os.path.abspath(__file__))
        bg_path = os.path.join(current_dir, 'poddle_v3.png')
        
        try:
            self.bg_image = pygame.image.load(bg_path).convert()
            self.bg_image = pygame.transform.scale(self.bg_image, (self.width, self.height))
            self.has_bg = True
            print("Poodle Arka Planı Başarıyla Yüklendi.")
        except Exception as e:
            print(f"HATA: Görsel yüklenemedi: {e}")
            self.has_bg = False
            self.COLOR_BG = (10, 10, 15)

        # RENKLER (Siyah Gözler)
        self.EYE_COLOR = (5, 5, 5) 
        self.PUPIL_COLOR = (245, 245, 250) 
        
        self.eye_pos = [0, 0]
        self.target_pos = [0, 0]
        self.eye_scale_y = 1.0 
        self.target_scale_y = 1.0
        self.state = "idle" 
        self.last_blink = pygame.time.get_ticks()

    def set_state(self, state):
        self.state = state
        self.target_scale_y = 1.25 if state == "listening" else 0.90 if state == "speaking" else 1.0

    def update_gaze(self, tx, ty):
        if tx is not None and ty is not None:
            # Bakışın yuvadan taşmaması için hareketi kısıtlıyoruz
            self.target_pos = [(tx - self.width//2) / 60, (ty - self.height//2) / 60]
        else:
            self.target_pos = [0, 0]

    def draw(self, screen):
        if self.has_bg:
            screen.blit(self.bg_image, (0, 0))
        else:
            screen.fill(self.COLOR_BG)
        
        # Pürüzsüz geçişler
        self.eye_pos[0] += (self.target_pos[0] - self.eye_pos[0]) * 0.12
        self.eye_pos[1] += (self.target_pos[1] - self.eye_pos[1]) * 0.12
        self.eye_scale_y += (self.target_scale_y - self.eye_scale_y) * 0.15

        # Göz Kırpma Animasyonu
        now = pygame.time.get_ticks()
        if now - self.last_blink > random.randint(3000, 7000):
            self.eye_scale_y = 0.05
            if now - self.last_blink > 3150: self.last_blink = now

        # --- SENİN VERDİĞİN NOKTA ATIŞI KOORDİNATLAR ---
        left_eye_center = (348, 303)
        right_eye_center = (675, 303)
        
        # Senin istediğin boyut: 94 x 190
        eye_w, eye_h = 94, 190 * self.eye_scale_y

        for base_x, base_y in [left_eye_center, right_eye_center]:
            x = base_x + self.eye_pos[0]
            y = base_y + self.eye_pos[1]
            
            # Siyah Göz Kapsülü
            rect = pygame.Rect(x - eye_w//2, y - eye_h//2, eye_w, eye_h)
            pygame.draw.ellipse(screen, self.EYE_COLOR, rect)
            
            # Beyaz Parlama (Gözlerin canlı durması için şart)
            px = x + self.eye_pos[0] * 0.6
            py = y - eye_h//4 + self.eye_pos[1] * 0.4
            pygame.draw.ellipse(screen, self.PUPIL_COLOR, (px-10, py-8, 20, 16))
