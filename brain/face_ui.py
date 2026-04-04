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
            print(">>> [V7 - KALIBRASYON MODU] AKTIF <<<")
            print("OK TUSLARI ile gozleri kaydirabilirsin!")
        except:
            self.has_bg = False

        self.EYE_COLOR = (15, 15, 15) 
        self.PUPIL_COLOR = (255, 255, 255)
        
        # --- KALİBRASYON DEĞİŞKENLERİ ---
        # Bu değerleri ok tuşlarıyla değiştireceğiz
        self.offset_x = 0
        self.offset_y = -5 # Başlangıçta biraz yukarıda başlasın
        
        self.eye_scale_y = 1.0 
        self.target_scale_y = 1.0
        self.state = "idle" 
        self.last_blink = pygame.time.get_ticks()

    def set_state(self, state):
        self.state = state
        self.target_scale_y = 1.25 if state == "listening" else 0.90 if state == "speaking" else 1.0

    def handle_calibration(self, key):
        """Ok tuşlarıyla gözleri milimetrik kaydırır"""
        step = 2
        if key == pygame.K_UP: self.offset_y -= step
        if key == pygame.K_DOWN: self.offset_y += step
        if key == pygame.K_LEFT: self.offset_x -= step
        if key == pygame.K_RIGHT: self.offset_x += step
        
        # Yeni koordinatları terminale bas ki not edebilesin
        print(f"Guncel Hizalama -> X Kayma: {self.offset_x} | Y Kayma: {self.offset_y}")

    def update_gaze(self, tx, ty):
        # Kalibrasyon yaparken bakış takibini stabilize ediyoruz
        pass

    def draw(self, screen):
        if self.has_bg:
            screen.blit(self.bg_image, (0, 0))
        
        # Animasyonlar
        self.eye_scale_y += (self.target_scale_y - self.eye_scale_y) * 0.1
        now = pygame.time.get_ticks()
        if now - self.last_blink > random.randint(3000, 8000):
            self.eye_scale_y = 0.05
            if now - self.last_blink > 3150: self.last_blink = now

        # --- MERKEZ NOKTALAR + SENİN OK TUŞLARINLA GELEN KAYMA ---
        # Senin verdiğin 348 ve 675 değerlerine offsetleri ekliyoruz
        l_center = (348 + self.offset_x, 303 + self.offset_y)
        r_center = (675 + self.offset_x, 303 + self.offset_y)
        
        w, h = 94, 190 * self.eye_scale_y

        for cx, cy in [l_center, r_center]:
            # Göz
            pygame.draw.ellipse(screen, self.EYE_COLOR, (cx - w//2, cy - h//2, w, h))
            # Parlama
            if self.eye_scale_y > 0.4:
                pygame.draw.ellipse(screen, self.PUPIL_COLOR, (cx - 10, cy - h//3.5, 20, 15))
