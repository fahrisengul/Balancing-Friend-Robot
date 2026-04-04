import pygame
import math
import random

class PoodleFace:
    def __init__(self, width=1024, height=600):
        self.width = width
        self.height = height
        
        # --- MODERN RENK PALETİ (Cyber-Cyan & Deep Black) ---
        self.COLOR_BG = (10, 12, 18)
        self.EYE_COLOR = (0, 255, 255) # Canlı Turkuaz (AI Rengi)
        self.GLOW_COLOR = (0, 100, 100)
        
        # --- DURUM VE HAREKET ---
        self.eye_pos = [0, 0]
        self.target_pos = [0, 0]
        self.eye_scale_y = 1.0 # Göz kapakları için
        self.target_scale_y = 1.0
        
        self.state = "idle" # idle, listening, speaking
        self.last_blink = pygame.time.get_ticks()

    def set_state(self, state):
        self.state = state
        if state == "listening":
            self.target_scale_y = 1.2 # Heyecanlı/Dikkatli
        elif state == "speaking":
            self.target_scale_y = 0.9 # Odaklanmış
        else:
            self.target_scale_y = 1.0

    def update_gaze(self, tx, ty):
        if tx:
            self.target_pos = [(tx - 320) / 4, (ty - 240) / 4]
        else:
            # Boştayken hafif salınım (Canlılık hissi)
            self.target_pos = [math.sin(pygame.time.get_ticks()*0.002)*10, 0]

    def draw(self, screen):
        screen.fill(self.COLOR_BG)
        
        # --- LERP (Pürüzsüz Geçiş) ---
        self.eye_pos[0] += (self.target_pos[0] - self.eye_pos[0]) * 0.1
        self.eye_pos[1] += (self.target_pos[1] - self.eye_pos[1]) * 0.1
        self.eye_scale_y += (self.target_scale_y - self.eye_scale_y) * 0.1

        # --- GÖZ KIRPMA ---
        now = pygame.time.get_ticks()
        if now - self.last_blink > random.randint(3000, 7000):
            self.eye_scale_y = 0.1 # Gözü kapat
            if now - self.last_blink > 3150:
                self.last_blink = now

        # --- GÖZLERİ ÇİZ (Modern Capsule Shape) ---
        for side in [-1, 1]:
            x = (self.width // 2) + (side * 180) + self.eye_pos[0]
            y = (self.height // 2) + self.eye_pos[1]
            
            # Göz Boyutları
            w, h = 140, 200 * self.eye_scale_y
            
            # 1. Dış Parlama (Glow)
            for i in range(3):
                pygame.draw.ellipse(screen, self.GLOW_COLOR, (x-w//2-i*5, y-h//2-i*5, w+i*10, h+i*10), 2)
            
            # 2. Ana Göz (Kapsül)
            rect = pygame.Rect(x-w//2, y-h//2, w, h)
            pygame.draw.ellipse(screen, self.EYE_COLOR, rect)
            
            # 3. İç Parlama (Derinlik)
            pygame.draw.ellipse(screen, (255, 255, 255), (x-w//4, y-h//3, w//2, h//4))

        # --- SPEAKING MODUNDA SES DALGASI ---
        if self.state == "speaking":
            wave = abs(math.sin(pygame.time.get_ticks()*0.02)) * 40
            pygame.draw.rect(screen, self.EYE_COLOR, (self.width//2 - 50, self.height - 100, 100, 10 + wave), border_radius=5)
