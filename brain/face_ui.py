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
            print(">>> [V8 - DARALTILMIS SIYAH GOZLER] AKTIF <<<")
        except:
            self.has_bg = False

        self.EYE_COLOR = (15, 15, 15) 
        self.PUPIL_COLOR = (255, 255, 255)
        
        # --- KALIBRASYON ---
        self.offset_x = 0
        self.offset_y = -5 
        
        self.eye_scale_y = 1.0 
        self.target_scale_y = 1.0
        self.state = "idle" 
        self.last_blink = pygame.time.get_ticks()

    def set_state(self, state):
        self.state = state
        self.target_scale_y = 1.25 if state == "listening" else 0.90 if state == "speaking" else 1.0

    def handle_calibration(self, key):
        step = 1 # Daha hassas ayar için adımı 1'e düşürdüm
        if key == pygame.K_UP: self.offset_y -= step
        if key == pygame.K_DOWN: self.offset_y += step
        if key == pygame.K_LEFT: self.offset_x -= step
        if key == pygame.K_RIGHT: self.offset_x += step
        print(f"Hizalama -> X: {self.offset_x} | Y: {self.offset_y}")

    def update_gaze(self, tx, ty):
        # Gozlerin yuvada cok hafif oynamasi icin boleni artirdim (120)
        if tx is not None and ty is not None:
            self.target_pos = [(tx - self.width//2) / 120, (ty - self.height//2) / 120]
        else:
            self.target_pos = [0, 0]

    def draw(self, screen):
        if self.has_bg:
            screen.blit(self.bg_image, (0, 0))
        
        # Animasyon LERP
        self.eye_scale_y += (self.target_scale_y - self.eye_scale_y) * 0.1
        
        # Goz Kirpma
        now = pygame.time.get_ticks()
        if now - self.last_blink > random.randint(3000, 8000):
            self.eye_scale_y = 0.05
            if now - self.last_blink > 3150: self.last_blink = now

        # --- DARALTILMIS GOZ BOYUTLARI ---
        # Genislik: 94 -> 70 | Yukseklik: 190 -> 140 (Daha kompakt)
        w, h = 70, 140 * self.eye_scale_y
        
        l_center = (348 + self.offset_x, 303 + self.offset_y)
        r_center = (675 + self.offset_x, 303 + self.offset_y)

        for cx, cy in [l_center, r_center]:
            # Siyah Goz
            pygame.draw.ellipse(screen, self.EYE_COLOR, (cx - w//2, cy - h//2, w, h))
            
            # Parlama (Pupil) - Goz kuculdugu icin parlama boyutunu da kuculttum
            if self.eye_scale_y > 0.4:
                pygame.draw.ellipse(screen, self.PUPIL_COLOR, (cx - 6, cy - h//3, 12, 10))
