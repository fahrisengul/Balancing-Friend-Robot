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
        # Dosya isminin 'poddle_v3.png' olduğundan emin ol
        bg_path = os.path.join(current_dir, 'poddle_v3.png')
        
        try:
            self.bg_image = pygame.image.load(bg_path).convert()
            # Görseli ekran boyutuna ölçekle
            self.bg_image = pygame.transform.scale(self.bg_image, (self.width, self.height))
            self.has_bg = True
        except Exception as e:
            print(f"UYARI: Arka plan yüklenemedi: {e}")
            self.has_bg = False
            self.COLOR_BG = (10, 12, 18) # Yedek siyah arka plan

        # --- RENKLER ---
        self.EYE_COLOR = (0, 255, 255) # AI Turkuazı
        self.GLOW_COLOR = (0, 100, 100)
        
        # --- DURUM VE HAREKET ---
        self.eye_pos = [0, 0]
        self.target_pos = [0, 0]
        self.eye_scale_y = 1.0 
        self.target_scale_y = 1.0
        
        self.state = "idle" 
        self.last_blink = pygame.time.get_ticks()

    def set_state(self, state):
        self.state = state
        self.target_scale_y = 1.2 if state == "listening" else 0.9 if state == "speaking" else 1.0

    def update_gaze(self, tx, ty):
        if tx is not None and ty is not None:
            # Bakış kaymasını, kafadaki turkuaz yuvaların içinde kalacak şekilde kısıtlıyoruz (±10px)
            self.target_pos = [(tx / 32) - 10, (ty / 24) - 10]
        else:
            # Boştayken hafif salınım (Canlılık hissi)
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
            self.eye_scale_y = 0.1 # Gözü kapat
            if now - self.last_blink > 3150:
                self.last_blink = now

        # --- GÖZLERİ ÇİZ (Güncellenmiş Konum ve Boyut) ---
        # Gözleri birbirine yaklaştırarak (ortaya alarak) çiziyoruz
        # Genişliği ve yüksekliği de orantılı olarak küçülttük.
        centers = [(self.width // 2 - 120, self.height // 2 - 5), # Sol göz merkezi
                   (self.width // 2 + 120, self.height // 2 - 5)] # Sağ göz merkezi

        for base_x, base_y in centers:
            x = base_x + self.eye_pos[0]
            y = base_y + self.eye_pos[1]
            
            # Göz Boyutları (poddle_v3'teki mavi harelere sığacak kadar)
            w, h = 100, 160 * self.eye_scale_y
            
            # 1. Parlama (Glow)
            for i in range(2): # Glow katmanını azalttık (hafifletmek için)
                pygame.draw.ellipse(screen, self.GLOW_COLOR, (x-w//2-i*5, y-h//2-i*5, w+i*10, h+i*10), 2)
            
            # 2. Ana Göz (Kapsül)
            rect = pygame.Rect(x-w//2, y-h//2, w, h)
            pygame.draw.ellipse(screen, self.EYE_COLOR, rect)
            
            # 3. Derinlik Işığı (Pupil)
            # Bu nokta bakış yönüne göre biraz daha az kayar (3D derinlik hissi)
            pupil_x = x + self.eye_pos[0] * 0.5
            pupil_y = y - h//4 + self.eye_pos[1] * 0.5
            pygame.draw.ellipse(screen, (255, 255, 255), (pupil_x-12, pupil_y-10, 25, 20))

        # --- SES DALGASI (Speaking modunda) ---
        if self.state == "speaking":
            wave = abs(math.sin(pygame.time.get_ticks()*0.02)) * 40
            pygame.draw.rect(screen, self.EYE_COLOR, (self.width//2 - 50, self.height - 100, 100, 10 + wave), border_radius=5)
