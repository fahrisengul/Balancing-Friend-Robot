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
        bg_path = os.path.join(current_dir, 'Poddle_v2.jpeg')
        
        try:
            # Görseli yükle ve ekran boyutuna ölçekle
            self.bg_image = pygame.image.load(bg_path)
            self.bg_image = pygame.transform.scale(self.bg_image, (self.width, self.height))
            self.has_bg = True
        except:
            print("UYARI: Poddle_v2.jpeg bulunamadı, siyah arka plana dönülüyor.")
            self.has_bg = False
            self.COLOR_BG = (10, 12, 18)

        # --- MODERN RENK PALETİ ---
        self.EYE_COLOR = (0, 255, 255) # Orijinal Poodle Mavisi
        self.GLOW_COLOR = (0, 100, 100, 128) # Yarı şeffaf parlama
        
        # --- DURUM VE HAREKET ---
        self.eye_pos = [0, 0]
        self.target_pos = [0, 0]
        self.eye_scale_y = 1.0 
        self.target_scale_y = 1.0
        
        self.state = "idle" 
        self.last_blink = pygame.time.get_ticks()

    def set_state(self, state):
        self.state = state
        if state == "listening":
            self.target_scale_y = 1.15 
        elif state == "speaking":
            self.target_scale_y = 0.95
        else:
            self.target_scale_y = 1.0

    def update_gaze(self, tx, ty):
        if tx is not None and ty is not None:
            # Gözlerin hareket sınırını Poddle_v2 yuvaları içinde tutmak için (±30px)
            self.target_pos = [(tx - 320) / 10, (ty - 240) / 12]
        else:
            # Boştayken çok hafif nefes alma efekti
            self.target_pos = [math.sin(pygame.time.get_ticks()*0.001)*5, math.cos(pygame.time.get_ticks()*0.001)*3]

    def draw(self, screen):
        # 1. Arka Planı Çiz
        if self.has_bg:
            screen.blit(self.bg_image, (0, 0))
        else:
            screen.fill(self.COLOR_BG)
        
        # --- LERP (Pürüzsüz Geçiş) ---
        self.eye_pos[0] += (self.target_pos[0] - self.eye_pos[0]) * 0.1
        self.eye_pos[1] += (self.target_pos[1] - self.eye_pos[1]) * 0.1
        self.eye_scale_y += (self.target_scale_y - self.eye_scale_y) * 0.1

        # --- GÖZ KIRPMA ---
        now = pygame.time.get_ticks()
        if now - self.last_blink > random.randint(4000, 9000):
            self.eye_scale_y = 0.05
            if now - self.last_blink > 4150:
                self.last_blink = now

        # --- GÖZLERİ ÇİZ (Poddle_v2 Tasarımına Uygun) ---
        for side in [-1, 1]:
            # Görseldeki yuvaların merkezi (1024x600'e göre ayarlandı)
            base_x = (self.width // 2) + (side * 182) 
            base_y = (self.height // 2) - 10
            
            x = base_x + self.eye_pos[0]
            y = base_y + self.eye_pos[1]
            
            # Göz boyutlarını Poddle_v2'deki halkalara göre daralttık (Daha şık durur)
            w, h = 100, 160 * self.eye_scale_y
            
            # 1. Yumuşak Dış Parlama (Glow)
            glow_surface = pygame.Surface((w*2, h*2), pygame.SRCALPHA)
            pygame.draw.ellipse(glow_surface, (0, 255, 255, 40), (w//2, h//2, w, h))
            screen.blit(glow_surface, (x-w, y-h))
            
            # 2. Ana Göz (Hafif Şeffaf Turkuaz)
            rect = pygame.Rect(x-w//2, y-h//2, w, h)
            pygame.draw.ellipse(screen, self.EYE_COLOR, rect)
            
            # 3. Göz Bebeği / Işıma (Beyaz Nokta)
            # Bu nokta bakış yönüne göre biraz daha fazla kayar (3D derinlik hissi)
            pupil_x = x + self.eye_pos[0] * 0.5
            pupil_y = y - h//4 + self.eye_pos[1] * 0.5
            pygame.draw.ellipse(screen, (255, 255, 255), (pupil_x-15, pupil_y-10, 30, 20))

        # --- SPEAKING MODUNDA SES DALGASI ---
        if self.state == "speaking":
            wave = abs(math.sin(pygame.time.get_ticks()*0.02)) * 30
            # Alt kısımdaki boşluğa estetik bir bar
            pygame.draw.rect(screen, self.EYE_COLOR, (self.width//2 - 40, self.height - 80, 80, 6 + wave), border_radius=10)
