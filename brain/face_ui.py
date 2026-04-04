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
        #image_1.png'nin bulunduğu tam yol. Dosya adı uzantısını kontrol et (.png/.jpg)
        bg_path = os.path.join(current_dir, 'Poddle_v2.jpeg') 
        
        try:
            self.bg_image = pygame.image.load(bg_path).convert()
            self.bg_image = pygame.transform.scale(self.bg_image, (self.width, self.height))
            self.has_bg = True
        except Exception as e:
            print(f"UYARI: Arka plan yüklenemedi: {e}")
            self.has_bg = False
            self.COLOR_BG = (10, 12, 18) # Yedek siyah arka plan

        # --- RENKLER VE DURUM ---
        # image_3.png'deki turkuaz AI mavisi
        self.EYE_COLOR = (0, 255, 255) 
        self.GLOW_COLOR = (0, 100, 100)
        
        # --- HAREKET DEĞİŞKENLERİ ---
        self.eye_pos = [0, 0]
        self.target_pos = [0, 0]
        self.eye_scale_y = 1.0 
        self.target_scale_y = 1.0
        
        self.state = "idle" 
        self.last_blink = pygame.time.get_ticks()

    def set_state(self, state):
        """main.py'den gelen konuşma/dinleme modunu ayarlar"""
        self.state = state
        if state == "listening":
            self.target_scale_y = 1.15 # Biraz daha açık gözler
        elif state == "speaking":
            self.target_scale_y = 0.95 # Odaklanmış gözler
        else:
            self.target_scale_y = 1.0

    def update_gaze(self, tx, ty):
        """Yüz takip koordinatlarını (tx, ty) alır"""
        if tx is not None and ty is not None:
            # Bakış kaymasını, kafadaki turkuaz yuvaların içinde kalacak şekilde kısıtlıyoruz (±20px)
            # 640x480 kamera koordinatlarını ±20px aralığına normalize ediyoruz.
            self.target_pos = [(tx / 16) - 20, (ty / 12) - 20]
        else:
            # Boştayken çok hafif, canlı bir nefes alma efekti
            t = pygame.time.get_ticks()
            self.target_pos = [math.sin(t*0.001)*10, math.cos(t*0.001)*5]

    def draw(self, screen):
        """Her döngüde ekranı çizer"""
        # 1. Arka Planı Çiz
        if self.has_bg:
            screen.blit(self.bg_image, (0, 0))
        else:
            screen.fill(self.COLOR_BG)
        
        # --- LERP (Pürüzsüz Hareket Geçişi) ---
        self.eye_pos[0] += (self.target_pos[0] - self.eye_pos[0]) * 0.1
        self.eye_pos[1] += (self.target_pos[1] - self.eye_pos[1]) * 0.1
        self.eye_scale_y += (self.target_scale_y - self.eye_scale_y) * 0.1

        # --- GÖZ KIRPMA ---
        now = pygame.time.get_ticks()
        if now - self.last_blink > random.randint(4000, 9000):
            self.eye_scale_y = 0.05 # Gözü kapat
            if now - self.last_blink > 4150: # Göz kapalı kalma süresi
                self.last_blink = now

        # --- GÖZLERİ ÇİZ ---
        # image_1.png üzerindeki AI turkuaz yuvaların tahmini merkez koordinatları
        # Bu koordinatlar, 1024x600 çözünürlüğünde tam o yuvalara denk gelmelidir.
        left_eye_center = (454, 252)
        right_eye_center = (570, 252)

        for side in [-1, 1]: # -1 Sol, 1 Sağ
            if side == -1:
                base_x, base_y = left_eye_center
            else:
                base_x, base_y = right_eye_center
            
            x = base_x + self.eye_pos[0]
            y = base_y + self.eye_pos[1]
            
            # Göz Boyutları (image_3.png'deki yuvaların içine sığacak kadar)
            w, h = 90, 150 * self.eye_scale_y
            
            # 1. Yumuşak Dış Parlama (Glow) - Yarı şeffaf
            glow_surface = pygame.Surface((w*2, h*2), pygame.SRCALPHA)
            pygame.draw.ellipse(glow_surface, (0, 255, 255, 40), (w//2, h//2, w, h))
            screen.blit(glow_surface, (x-w, y-h))
            
            # 2. Ana Göz (Kapsül)
            rect = pygame.Rect(x-w//2, y-h//2, w, h)
            pygame.draw.ellipse(screen, self.EYE_COLOR, rect)
            
            # 3. Göz Bebeği / Işıma (Beyaz Merkez)
            # Bakış derinliği hissi için bu nokta ana gözden biraz daha az kayar
            pupil_x = x + self.eye_pos[0] * 0.4
            pupil_y = y - h//4 + self.eye_pos[1] * 0.4
            pygame.draw.ellipse(screen, (255, 255, 255), (pupil_x-12, pupil_y-10, 25, 20))

        # --- SPEAKING MODUNDA SES DALGASI (Opsiyonel Estetik) ---
        if self.state == "speaking":
            wave = abs(math.sin(pygame.time.get_ticks()*0.02)) * 30
            # Alt kısımdaki boşluğa estetik bir bar
            pygame.draw.rect(screen, self.EYE_COLOR, (self.width//2 - 40, self.height - 80, 80, 6 + wave), border_radius=10)
