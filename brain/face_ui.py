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
            # BU YAZIYI GÖRMELİSİN:
            print(">>> [V6 - ANIMASYONLU & TAM HIZALI] CALISIYOR <<<")
        except:
            self.has_bg = False

        self.EYE_COLOR = (15, 15, 15) 
        self.PUPIL_COLOR = (255, 255, 255)
        
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
            # Bakışın yuvadan taşmaması için daraltılmış hareket
            self.target_pos = [(tx - self.width//2) / 80, (ty - self.height//2) / 80]
        else:
            self.target_pos = [0, 0]

    def draw(self, screen):
        if self.has_bg:
            screen.blit(self.bg_image, (0, 0))
        
        # Pürüzsüz geçişler
        self.eye_pos[0] += (self.target_pos[0] - self.eye_pos[0]) * 0.1
        self.eye_pos[1] += (self.target_pos[1] - self.eye_pos[1]) * 0.1
        self.eye_scale_y += (self.target_scale_y - self.eye_scale_y) * 0.1

        # Göz Kırpma (150ms sürer)
        now = pygame.time.get_ticks()
        if now - self.last_blink > random.randint(3000, 8000):
            self.eye_scale_y = 0.05
            if now - self.last_blink > 3150:
                self.last_blink = now

        # --- NOKTA ATIŞI KOORDİNATLAR (348, 303 ve 675, 303 merkezli) ---
        # Senin ölçülerini kullandım, sadece dikeyde halkaya tam oturtmak için 298 yaptım.
        centers = [(348, 298), (675, 298)]
        w, h = 94, 190 * self.eye_scale_y

        for cx, cy in centers:
            x_pos = cx + self.eye_pos[0]
            y_pos = cy + self.eye_pos[1]
            # Siyah Göz
            pygame.draw.ellipse(screen, self.EYE_COLOR, (x_pos - w//2, y_pos - h//2, w, h))
            # Parlama
            if self.eye_scale_y > 0.4:
                pygame.draw.ellipse(screen, self.PUPIL_COLOR, (x_pos - 10, y_pos - h//3, 20, 15))
