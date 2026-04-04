import pygame
import math
import random
import os

class PoodleFace:
    def __init__(self, width=1024, height=600):
        self.width = width
        self.height = height
        
        # --- ARKA PLAN YÜKLEME ---
        current_dir = os.path.dirname(os.path.abspath(__file__))
        bg_path = os.path.join(current_dir, 'Poddle_v3.png')
        
        try:
            self.bg_image = pygame.image.load(bg_path).convert()
            # Görseli 1024x600'e tam oturtuyoruz
            self.bg_image = pygame.transform.scale(self.bg_image, (self.width, self.height))
            self.has_bg = True
        except Exception as e:
            print(f"HATA: {bg_path} yüklenemedi: {e}")
            self.has_bg = False
            self.COLOR_BG = (15, 15, 25)

        # --- RENKLER ---
        self.EYE_COLOR = (0, 255, 255) # AI Turkuaz
        self.PUPIL_COLOR = (255, 255, 255) # Parlama noktası
        
        # --- DURUM VE HAREKET ---
        self.eye_pos = [0, 0]
        self.target_pos = [0, 0]
        self.eye_scale_y = 1.0 
        self.target_scale_y = 1.0
        self.state = "idle" 
        self.last_blink = pygame.time.get_ticks()

    def set_state(self, state):
        self.state = state
        # Modlara göre gözlerin büyüklüğü
        if state == "listening":
            self.target_scale_y = 1.2
        elif state == "speaking":
            self.target_scale_y = 0.95
        else:
            self.target_scale_y = 1.0

    def update_gaze(self, tx, ty):
        if tx is not None and ty is not None:
            # Göz yuvalarının içinde (±15px) pürüzsüz hareket alanı
            self.target_pos = [(tx - 320) / 15, (ty - 240) / 18]
        else:
            # Boştayken hafif canlılık salınımı
            t = pygame.time.get_ticks()
            self.target_pos = [math.sin(t*0.001)*6, math.cos(t*0.001)*3]

    def draw(self, screen):
        # 1. Arka Planı Çiz
        if self.has_bg:
            screen.blit(self.bg_image, (0, 0))
        else:
            screen.fill(self.COLOR_BG)
        
        # --- LERP (Yumuşak Geçiş) ---
        self.eye_pos[0] += (self.target_pos[0] - self.eye_pos[0]) * 0.1
        self.eye_pos[1] += (self.target_pos[1] - self.eye_pos[1]) * 0.1
        self.eye_scale_y += (self.target_scale_y - self.eye_scale_y) * 0.1

        # --- GÖZ KIRPMA ---
        now = pygame.time.get_ticks()
        if now - self.last_blink > random.randint(4000, 10000):
            self.eye_scale_y = 0.05
            if now - self.last_blink > 4150:
                self.last_blink = now

        # --- GÖZLERİ YUVALARA YERLEŞTİR ---
        # Poddle_v2.png üzerindeki yuva merkezleri (1024x600 için hassas ayar)
        # Sol yuva merkezi: 345, Sağ yuva merkezi: 679 (tahmini)
        centers = [(self.width // 2 - 168, self.height // 2 - 5), 
                   (self.width // 2 + 168, self.height // 2 - 5)]

        for base_x, base_y in centers:
            x = base_x + self.eye_pos[0]
            y = base_y + self.eye_pos[1]
            
            # Göz Boyutları (Yuvadaki koyu alana sığacak şekilde)
            w, h = 90, 150 * self.eye_scale_y
            
            # 1. Yumuşak İç Parlama (Glow)
            glow_surf = pygame.Surface((w*2, h*2), pygame.SRCALPHA)
            pygame.draw.ellipse(glow_surf, (0, 255, 255, 30), (w//2, h//2, w, h))
            screen.blit(glow_surf, (x-w, y-h))
            
            # 2. Ana Göz (Kapsül)
            pygame.draw.ellipse(screen, self.EYE_COLOR, (x-w//2, y-h//2, w, h))
            
            # 3. Canlılık Işığı (Pupil/Highlight)
            # Bakış yönüne göre ekstra kayarak derinlik (paralaks) sağlar
            px = x + self.eye_pos[0] * 0.6
            py = y - h//4 + self.eye_pos[1] * 0.4
            pygame.draw.ellipse(screen, self.PUPIL_COLOR, (px-12, py-10, 25, 18))

        # --- SPEAKING BAR (Alt kısımda estetik ses dalgası) ---
        if self.state == "speaking":
            wave = abs(math.sin(pygame.time.get_ticks()*0.02)) * 30
            pygame.draw.rect(screen, self.EYE_COLOR, 
                             (self.width//2 - 45, self.height - 70, 90, 8 + wave), 
                             border_radius=10)
