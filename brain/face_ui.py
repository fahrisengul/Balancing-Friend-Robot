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
            # BU YAZIYI TERMINALDE GORMELISIN:
            print(">>> [V4 - SIYAH GOZ MODU] AKTIF EDILDI <<<")
        except:
            self.has_bg = False

        # RENKLER (SIYAH)
        self.EYE_COLOR = (10, 10, 10) 
        self.PUPIL_COLOR = (255, 255, 255)
        self.state = "idle"

    def set_state(self, state):
        self.state = state

    def update_gaze(self, tx, ty):
        # Test asamasinda gozler sabit kalsin diye burayi kapattik
        pass 

    def draw(self, screen):
        if self.has_bg:
            screen.blit(self.bg_image, (0, 0))
        
        # --- MILIMETRIK KOORDINATLAR ---
        # Y eksenini 303'ten 255'e cektim (Biraz yukari aldim)
        left_center = (348, 255) 
        right_center = (675, 255)
        
        # Senin olculerin: 94 x 190
        w, h = 94, 190

        for cx, cy in [left_center, right_center]:
            # 1. Ana Goz (SIYAH)
            pygame.draw.ellipse(screen, self.EYE_COLOR, (cx - w//2, cy - h//2, w, h))
            
            # 2. Parlama (BEYAZ) - Gozun canli durmasi icin yukariya bir nokta
            pygame.draw.ellipse(screen, self.PUPIL_COLOR, (cx - 10, cy - 60, 20, 15))
