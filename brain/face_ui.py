import pygame
import math
import random
import os

class PoodleFace:
    def __init__(self, width=1024, height=600):
        self.width = width
        self.height = height
        
        # --- ARKA PLAN GÖRSELİ YÜKLEME ---
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # Dosya adının klasördekiyle birebir aynı (büyük/küçük harf) olduğundan emin ol
        bg_path = os.path.join(current_dir, 'Poddle_v2.jpeg')
        
        try:
            self.bg_image = pygame.image.load(bg_path).convert()
            self.bg_image = pygame.transform.scale(self.bg_image, (self.width, self.height))
            self.has_bg = True
        except Exception as e:
            print(f"UYARI: Arka plan yüklenemedi: {e}")
            self.has_bg = False
            self.COLOR_BG = (10, 12, 18)

        # --- RENKLER VE DURUM ---
        self.EYE_COLOR = (0, 255, 255) # Poodle Turkuazı
        self.GLOW_COLOR = (0, 100, 100)
        
        self.eye_pos = [0, 0]
        self.target_pos = [0, 0]
        self.eye_scale_y = 1.0 
        self.target_scale_y = 1.0
        
        self.state = "idle" 
        self.last_blink = pygame.time.get_ticks()

    def set_state(self, state):
        self.state = state
        if state == "listening":
            self.target_scale_y = 1.2
        elif state == "speaking":
            self.target_scale_y = 0.9
        else:
            self.target_scale_y = 1.0

    def update_gaze(self, tx, ty):
        if tx is not None and ty is not None:
            # Gözlerin hareket sınırını görseldeki yuvalara göre kısıtlıyoruz
            self.target_pos = [(tx - 320) / 8, (ty - 240) / 10]
        else:
            self.target_pos = [math.sin(pygame.time.get_ticks()*0.002)*10, 0]

    def draw(self, screen):
        # 1. Arka Planı Çiz
        if self.has_bg:
            screen.blit(self.bg_image, (0, 0))
        else:
            screen.fill(self.COLOR_BG)
        
        # --- LERP (Pürüzsüz Hareket) ---
        self.eye_pos[0] += (self.target_pos[0] - self.eye_pos[0]) * 0.1
        self.eye_pos[1] += (self.target_pos[1] - self.eye_pos[1]) * 0.1
        self.eye_scale_y += (self.target_scale_y - self.eye_scale_y) * 0.1

        # --- GÖZ KIRPMA ---
        now = pygame.time.get_ticks()
        if now - self.last_blink > random.randint(3000, 7000):
            self.eye_scale_y = 0.1
            if now - self.last_blink > 3150:
                self.last_blink = now

        # --- GÖZLERİ ÇİZ ---
        for side in [-1, 1]:
            # Görseldeki yuvaların merkezine göre konumlandırma (1024x600 için)
            base_x = (self.width // 2) + (side * 182) 
            base_y = (self.height // 2) - 10
            
            x = base_x + self.eye_pos[0]
            y = base_y + self.eye_pos[1]
            
            w, h = 130, 190 * self.eye_scale_y
            
            # Parlama (Glow)
            for i in range(3):
                pygame.draw.ellipse(screen, self.GLOW_COLOR, (x-w//2-i*5, y-h//2-i*5, w+i*10, h+i*10), 2)
            
            # Ana Göz (Kapsül)
            rect = pygame.Rect(x-w//2, y-h//2, w, h)
            pygame.draw.ellipse(screen, self.EYE_COLOR, rect)
            
            # Derinlik Işığı
            pygame.draw.ellipse(screen, (255, 255, 255), (x-w//4, y-h//3, w//2, h//4))

        # --- SES DALGASI ---
        if self.state == "speaking":
            wave = abs(math.sin(pygame.time.get_ticks()*0.02)) * 40
            pygame.draw.rect(screen, self.EYE_COLOR, (self.width//2 - 50, self.height - 100, 100, 10 + wave), border_radius=5)
