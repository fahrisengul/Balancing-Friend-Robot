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

        # --- RENKLER (Yeni İstek: Siyah) ---
        self.EYE_COLOR = (5, 5, 5) # Derin Siyah (Tam 0,0,0 yerine hafif dokulu)
        self.PUPIL_COLOR = (240, 240, 245) # Canlı beyaz parlama
        
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
            self.target_scale_y = 1.25 # Heyecanlı/Dikkatli bakış
        elif state == "speaking":
            self.target_scale_y = 0.90 # Odaklanmış bakış
        else:
            self.target_scale_y = 1.0

    def update_gaze(self, tx, ty):
        if tx and ty:
            # Gözlerin hareket sınırını, kafadaki mavi yuvanın içinde kalacak şekilde kısıtlıyoruz (±10px)
            # 640x480 kamera koordinatlarını ±10px aralığına normalize ediyoruz.
            self.target_pos = [(tx / 32) - 10, (ty / 24) - 10]
        else:
            # Boştayken hafif salınım (Canlılık hissi)
            t = pygame.time.get_ticks()
            self.target_pos = [math.sin(t*0.001)*4, math.cos(t*0.001)*2]

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
            self.eye_scale_y = 0.05 # Gözü kapat
            if now - self.last_blink > 3150: # Göz kapalı kalma süresi
                self.last_blink = now

        # --- GÖZLERİ ÇİZ (Güncellenmiş Konum ve Boyut) ---
        # poddle_v3'teki mavi hareli dairesel yuvaların merkez koordinatları
        # Yatayda tam simetrik (1024 / 2 ± 165px), dikeyde tam merkezde (600 / 2)
        centers = [(self.width // 2 - 165, self.height // 2 - 5), # Sol göz merkezi
                   (self.width // 2 + 165, self.height // 2 - 5)] # Sağ göz merkezi

        for base_x, base_y in centers:
            x = base_x + self.eye_pos[0]
            y = base_y + self.eye_pos[1]
            
            # Göz Boyutları (poddle_v3'teki dairesel yuvaların içine sığacak kadar)
            w, h = 90, 140 * self.eye_scale_y # Boyutları orantılı olarak küçülttük
            
            # 1. Parlama (Glow)
            # Dış parlamayı biraz daha hafiflettik (katman sayısını 2'ye düşürdük)
            # Glow_color'ı siyah gözler için değiştirmedik, hâlâ AI Turkuazı.
            for i in range(2): 
                pygame.draw.ellipse(screen, (0, 100, 100), (x-w//2-i*5, y-h//2-i*5, w+i*10, h+i*10), 2)
            
            # 2. Ana Göz (Derin Siyah)
            # Gözün kendisi (Kapsül) siyah.
            rect = pygame.Rect(x-w//2, y-h//2, w, h)
            pygame.draw.ellipse(screen, self.EYE_COLOR, rect)
            
            # 3. Derinlik Işığı (Pupil)
            # Bu nokta bakış yönüne göre biraz daha az kayar (3D derinlik hissi)
            pupil_x = x + self.eye_pos[0] * 0.5
            pupil_y = y - h//4 + self.eye_pos[1] * 0.5
            pygame.draw.ellipse(screen, self.PUPIL_COLOR, (pupil_x-12, pupil_y-10, 25, 20))

        # --- SES DALGASI (Speaking modunda) ---
        if self.state == "speaking":
            wave = abs(math.sin(pygame.time.get_ticks()*0.02)) * 40
            pygame.draw.rect(screen, self.EYE_COLOR, (self.width//2 - 50, self.height - 100, 100, 10 + wave), border_radius=5)
