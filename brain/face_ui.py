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
            print(">>> YENI KOORDINATLAR YUKLENDI: (348, 303)")
        except:
            self.has_bg = False

        self.EYE_COLOR = (5, 5, 5) # SIYAH
        self.PUPIL_COLOR = (250, 250, 250)
        self.state = "idle"
        self.eye_scale_y = 1.0

    def set_state(self, state):
        self.state = state

    def update_gaze(self, tx, ty):
        # TAKIP MODUNU TAMAMEN KAPATTIK (TEST ICIN)
        pass 

    def draw(self, screen):
        if self.has_bg:
            screen.blit(self.bg_image, (0, 0))
        
        # SENIN VERDIGIN NOKTA ATIŞI ÖLÇÜLER
        # Sol: 348, 303 | Sağ: 675, 303 | Boyut: 94x190
        left_center = (348, 303)
        right_center = (675, 303)
        w, h = 94, 190

        for cx, cy in [left_center, right_center]:
            # Siyah Göz
            pygame.draw.ellipse(screen, self.EYE_COLOR, (cx - w//2, cy - h//2, w, h))
            # Parlama (Pupil) - Tam sabit
            pygame.draw.ellipse(screen, self.PUPIL_COLOR, (cx - 5, cy - 40, 15, 12))
