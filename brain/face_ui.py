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
        # Dosya adının 'poddle_v3.png' olduğundan emin ol
        bg_path = os.path.join(current_dir, 'poddle_v3.png')
        
        try:
            self.bg_image = pygame.image.load(bg_path).convert()
            # Görseli tam ekran çözünürlüğüne ölçekle
            self.bg_image = pygame.transform.scale(self.bg_image, (self.width, self.height))
            self.has_bg = True
        except Exception as e:
            print(f"HATA: {bg_path} yüklenemedi: {e}")
            self.has_bg = False
            self.COLOR_BG = (10, 10, 15) # Yedek koyu arka plan

        # --- RENKLER (İstek üzerine siyah) ---
        self.EYE_COLOR = (5, 5, 5) # Derin Siyah (Tam 0,0,0 yerine hafif dokulu)
        self.PUPIL_COLOR = (245, 245, 250) # Canlı beyaz parlama
        
        # --- DURUM VE HAREKET ---
        self.eye_pos = [0, 0]
        self.target_pos = [0, 0]
        self.eye_scale_y = 1.0 
        self.target_scale_y = 1.0
        self.state = "idle" 
        self.last_blink = pygame.time.get_ticks()

    def set_state(self, state):
        """Robotun modunu (listening, speaking, idle) günceller"""
        self.state = state
        if state == "listening":
            self.target_scale_y = 1.25 # Daha dikkatli bakış
        elif state == "speaking":
            self.target_scale_y = 0.90 # Odaklanmış bakış
        else:
            self.target_scale_y = 1.0

    def update_gaze(self, tx, ty):
        """Yüz takip koordinatlarını (tx, ty) alır"""
        if tx is not None and ty is not None:
            # Bakış kaymasını, kafadaki turkuaz yuvanın içinde kalacak şekilde kısıtlıyoruz (±12px)
            # 640x480 kamera koordinatlarını bu aralığa normalize ediyoruz.
            self.target_pos = [(tx / 64) - 5, (ty / 48) - 5]
        else:
            # Boştayken çok hafif, canlı bir nefes alma efekti
            t = pygame.time.get_ticks()
            self.target_pos = [math.sin(t*0.0015)*4, math.cos(t*0.0015)*2]

    def draw(self, screen):
        """Her kareyi çizer"""
        # 1. Arka Planı Çiz
        if self.has_bg:
            screen.blit(self.bg_image, (0, 0))
        else:
            screen.fill(self.COLOR_BG)
        
        # --- LERP (Yumuşak Geçiş) ---
        self.eye_pos[0] += (self.target_pos[0] - self.eye_pos[0]) * 0.12
        self.eye_pos[1] += (self.target_pos[1] - self.eye_pos[1]) * 0.12
        self.eye_scale_y += (self.target_scale_y - self.eye_scale_y) * 0.15

        # --- GÖZ KIRPMA ---
        now = pygame.time.get_ticks()
        if now - self.last_blink > random.randint(3000, 7000):
            self.eye_scale_y = 0.05 # Gözü kapat
            if now - self.last_blink > 3150: # Göz kapalı kalma süresi
                self.last_blink = now

        # --- GÖZLERİ YUVALARA YERLEŞTİR (Senin Hassas Ölçülerin) ---
        # Sol yuva merkezi: (348, 303), Sağ yuva merkezi: (675, 303)
        left_eye_center = (348, 303)
        right_eye_center = (675, 303)

        for base_x, base_y in [left_eye_center, right_eye_center]:
            x = base_x + self.eye_pos[0]
            y = base_y + self.eye_pos[1]
            
            # Senin Göz Boyutların: 94 x 190 (Y ekseninde modlara göre ölçekleniyor)
            eye_w, eye_h = 94, 190 * self.eye_scale_y
            
            # 1. Hafif Dış Derinlik (Soft Shadow) - Siyah gözler için estetik gölge
            shadow_surface = pygame.Surface((eye_w*2, eye_h*2), pygame.SRCALPHA)
            pygame.draw.ellipse(shadow_surface, (0, 0, 0, 20), (eye_w//2+3, eye_h//2+5, eye_w, eye_h))
            screen.blit(shadow_surface, (x-eye_w, y-eye_h))
            
            # 2. Ana Göz (Derin Siyah Kapsül)
            rect = pygame.Rect(x-eye_w//2, y-eye_h//2, eye_w, eye_h)
            pygame.draw.ellipse(screen, self.EYE_COLOR, rect)
            
            # 3. Göz Bebeği / Işıma (Beyaz Merkez)
            # Derinlik hissi için bu nokta ana gözden biraz daha fazla kayar (Paralaks)
            pupil_x = x + self.eye_pos[0] * 0.6
            pupil_y = y - eye_h//4 + self.eye_pos[1] * 0.4
            pygame.draw.ellipse(screen, self.PUPIL_COLOR, (pupil_x-10, pupil_y-8, 20, 16))

        # --- SPEAKING MODUNDA SES DALGASI ---
        if self.state == "speaking":
            wave = abs(math.sin(pygame.time.get_ticks()*0.02)) * 35
            # Alt kısımdaki boşluğa estetik siyah/gri bir dalga
            pygame.draw.rect(screen, (30, 30, 30), (self.width//2 - 45, self.height - 70, 90, 8 + wave), border_radius=10)
