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
            print(">>> [V6 - ANIMASYONLU SIYAH GOZ] AKTIF <<<")
        except:
            self.has_bg = False

        # RENKLER (Derin Siyah ve Canlı Beyaz)
        self.EYE_COLOR = (15, 15, 15) 
        self.PUPIL_COLOR = (255, 255, 255)
        
        # --- HAREKET VE ANIMASYON DEĞİŞKENLERİ ---
        self.eye_pos = [0, 0]
        self.target_pos = [0, 0]
        self.eye_scale_y = 1.0 
        self.target_scale_y = 1.0
        self.state = "idle" 
        self.last_blink = pygame.time.get_ticks()

    def set_state(self, state):
        self.state = state
        # Modlara göre gözlerin açıklık oranı
        self.target_scale_y = 1.25 if state == "listening" else 0.90 if state == "speaking" else 1.0

    def update_gaze(self, tx, ty):
        # Hareket alanını çok daralttım ki yuvadan taşmasın
        if tx is not None and ty is not None:
            self.target_pos = [(tx - self.width//2) / 80, (ty - self.height//2) / 80]
        else:
            # Boştayken çok hafif bir "nefes alma" salınımı
            self.target_pos = [0, math.sin(pygame.time.get_ticks()*0.002)*2]

    def draw(self, screen):
        if self.has_bg:
            screen.blit(self.bg_image, (0, 0))
        
        # --- PÜRÜZSÜZ GEÇİŞLER (LERP) ---
        self.eye_pos[0] += (self.target_pos[0] - self.eye_pos[0]) * 0.1
        self.eye_pos[1] += (self.target_pos[1] - self.eye_pos[1]) * 0.1
        self.eye_scale_y += (self.target_scale_y - self.eye_scale_y) * 0.1

        # --- GÖZ KIRPMA MEKANİZMASI ---
        now = pygame.time.get_ticks()
        if now - self.last_blink > random.randint(3000, 8000):
            self.eye_scale_y = 0.05 # Gözü kapat
            if now - self.last_blink > 3150: # 150ms sonra tekrar aç
                self.last_blink = now

        # --- NOKTA ATIŞI KOORDİNATLAR (Görüntüye göre yukarı çekildi) ---
        # Y eksenini 303'ten 285'e çektim (Önceki 253 çok yukarıda olabilir diye ortaladım)
        left_center = (348, 285) 
        right_center = (675, 285)
        w, h = 94, 190 * self.eye_scale_y # Yükseklik scale ile çarpılıyor (Kırpma için)

        for cx, cy in [left_center, right_center]:
            # 1. Ana Göz (SIYAH)
            x_pos = cx + self.eye_pos[0]
            y_pos = cy + self.eye_pos[1]
            pygame.draw.ellipse(screen, self.EYE_COLOR, (x_pos - w//2, y_pos - h//2, w, h))
            
            # 2. Parlama (BEYAZ) - Sadece gözler açıkken görünsün
            if self.eye_scale_y > 0.3:
                # Parlama noktası gözün üst yarısında durur
                pygame.draw.ellipse(screen, self.PUPIL_COLOR, (x_pos - 10, y_pos - h//3, 20, 15))
