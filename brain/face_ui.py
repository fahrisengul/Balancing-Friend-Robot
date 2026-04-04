import pygame
import math
import random
import os

class PoodleFace:
    def __init__(self, width=1024, height=600):
        self.width = width
        self.height = height
        
        current_dir = os.path.dirname(os.path.abspath(__file__))
        bg_path = os.path.join(current_dir, 'Poddle_v2.jpeg')
        
        try:
            self.bg_image = pygame.image.load(bg_path).convert()
            self.bg_image = pygame.transform.scale(self.bg_image, (self.width, self.height))
            self.has_bg = True
        except:
            print("UYARI: Poddle_v2.jpeg bulunamadı, siyah arka plana dönülüyor.")
            self.has_bg = False
            self.COLOR_BG = (10, 12, 18)

        # Gözlerin temel konumu (Mavi yuvaların tahmini merkezleri)
        self.left_eye_center = (450, 240) # Mavi yuvanın merkezi (tahmini)
        self.right_eye_center = (574, 240) # Mavi yuvanın merkezi (tahmini)

        self.eye_color = (0, 255, 255) # Orijinal Poodle Mavisi
        self.glow_color = (0, 100, 100)
        
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
        if tx and ty:
            # Bakış kaymasını, kafadaki mavi yuvanın içinde kalacak şekilde küçültüyoruz (±5px)
            # 640x480 kamera koordinatlarını ±5px aralığına normalize ediyoruz.
            self.target_pos = [(tx / 64) - 5, (ty / 48) - 5]
        else:
            # Boştayken çok hafif nefes alma efekti
            self.target_pos = [math.sin(pygame.time.get_ticks()*0.001)*3, math.cos(pygame.time.get_ticks()*0.001)*2]

    def draw(self, screen):
        if self.has_bg:
            screen.blit(self.bg_image, (0, 0))
        else:
            screen.fill(self.COLOR_BG)
        
        # Pürüzsüz geçiş (Lerp)
        self.eye_pos[0] += (self.target_pos[0] - self.eye_pos[0]) * 0.1
        self.eye_pos[1] += (self.target_pos[1] - self.eye_pos[1]) * 0.1
        self.eye_scale_y += (self.target_scale_y - self.eye_scale_y) * 0.1

        # Göz kırpma
        now = pygame.time.get_ticks()
        if now - self.last_blink > random.randint(3000, 7000):
            self.eye_scale_y = 0.1
            if now - self.last_blink > 3150:
                self.last_blink = now

        # Gözleri kafadaki mavi halkaların içine çiziyoruz
        # Sol Göz (Left Eye)
        eye_w, eye_h = 30, 40 # Boyutları küçülttük (yuvanın içine sığacak kadar)
        eye_x = self.left_eye_center[0] + self.eye_pos[0]
        eye_y = self.left_eye_center[1] + self.eye_pos[1]
        rect_left = pygame.Rect(eye_x - eye_w//2, eye_y - eye_h//2, eye_w, eye_h * self.eye_scale_y)
        pygame.draw.ellipse(screen, self.eye_color, rect_left)
        # Derinlik Işığı (Pupil)
        pygame.draw.ellipse(screen, (255, 255, 255), (eye_x-eye_w//4, eye_y-eye_h//3, eye_w//2, eye_h//4))

        # Sağ Göz (Right Eye)
        eye_x = self.right_eye_center[0] + self.eye_pos[0]
        eye_y = self.right_eye_center[1] + self.eye_pos[1]
        rect_right = pygame.Rect(eye_x - eye_w//2, eye_y - eye_h//2, eye_w, eye_h * self.eye_scale_y)
        pygame.draw.ellipse(screen, self.eye_color, rect_right)
        # Derinlik Işığı (Pupil)
        pygame.draw.ellipse(screen, (255, 255, 255), (eye_x-eye_w//4, eye_y-eye_h//3, eye_w//2, eye_h//4))

        # Ses Dalgaları (Speaking modunda)
        if self.state == "speaking":
            wave = abs(math.sin(pygame.time.get_ticks()*0.02)) * 30
            pygame.draw.rect(screen, self.eye_color, (self.width//2 - 50, self.height - 100, 100, 10 + wave), border_radius=5)
