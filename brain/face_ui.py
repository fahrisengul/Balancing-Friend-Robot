import pygame
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
            # BU YAZIYI GÖRÜYORSAN YENİ KOD ÇALIŞIYORDUR
            print(">>> [V5 - SIYAH GOZ & YUKARI MERKEZ] AKTIF <<<")
        except:
            self.has_bg = False

        self.EYE_COLOR = (15, 15, 15) # SIYAH
        self.PUPIL_COLOR = (255, 255, 255) # BEYAZ PARLAMA
        self.state = "idle"

    def set_state(self, state):
        self.state = state

    def update_gaze(self, tx, ty):
        pass # Test için sabit tutuyoruz

    def draw(self, screen):
        if self.has_bg:
            screen.blit(self.bg_image, (0, 0))
        
        # --- MILIMETRIK AYARLANMIS KOORDINATLAR ---
        # Y eksenini 303'ten 253'e cektim (Yukari aldım)
        left_center = (348, 253) 
        right_center = (675, 253)
        w, h = 94, 190

        for cx, cy in [left_center, right_center]:
            # 1. Ana Göz (SIYAH)
            pygame.draw.ellipse(screen, self.EYE_COLOR, (cx - w//2, cy - h//2, w, h))
            # 2. Parlama (BEYAZ)
            pygame.draw.ellipse(screen, self.PUPIL_COLOR, (cx - 10, cy - 65, 20, 15))
