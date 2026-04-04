import pygame
import random

class PoodleFace:
    def __init__(self, width=1024, height=600):
        self.width = width
        self.height = height
        
        # 1. GÖRSELİ YÜKLE
        try:
            # Dosya adının klasördekiyle birebir aynı olduğundan emin olun
            self.poodle_img = pygame.image.load("image_21400b.jpg") 
            self.poodle_img = pygame.transform.scale(self.poodle_img, (width, height))
            print("Poodle görseli başarıyla yüklendi.")
        except:
            print("Hata: image_21400b.jpg bulunamadı! Siyah arka plan kullanılıyor.")
            self.poodle_img = None

        # 2. GÖZ KOORDİNATLARI (Resimdeki gözlerin tam üzeri)
        # Not: Resme göre bu X, Y değerlerini ufak ufak değiştirebiliriz.
        self.left_eye_center = [425, 290] 
        self.right_eye_center = [595, 290]
        
        # Göz hareket sınırları
        self.pupil_offset = [0, 0]
        
        # Göz Kırpma Ayarları
        self.is_blinking = False
        self.last_blink = pygame.time.get_ticks()
        self.next_blink_time = random.randint(3000, 6000)

    def update_gaze(self, target_x, target_y):
        """Kameradan gelen (640x480 tabanlı) koordinatları göz hareketine çevirir."""
        if target_x is None:
            self.pupil_offset = [0, 0] # Kimse yoksa merkeze bak
            return

        # Kameradaki merkeze (320, 240) uzaklığı hesapla ve küçült
        # (Göz bebeklerinin çok dışarı çıkmaması için 15 piksel sınır koyuyoruz)
        dx = (target_x - 320) / 20
        dy = (target_y - 240) / 20
        
        self.pupil_offset[0] = max(-15, min(15, dx))
        self.pupil_offset[1] = max(-10, min(10, dy))

    def draw(self, screen):
        # Önce Arka Planı (Resmi) Çiz
        if self.poodle_img:
            screen.blit(self.poodle_img, (0, 0))
        else:
            screen.fill((10, 10, 10))

        # Göz Kırpma Zamanlaması
        now = pygame.time.get_ticks()
        if now - self.last_blink > self.next_blink_time:
            self.is_blinking = True
            if now - self.last_blink > self.next_blink_time + 150: # 150ms kapalı kalsın
                self.is_blinking = False
                self.last_blink = now
                self.next_blink_time = random.randint(3000, 8000)

        # Gözleri Çiz
        for center in [self.left_eye_center, self.right_eye_center]:
            if self.is_blinking:
                # Göz kapalıyken: Resimdeki gözün üzerine ten rengine yakın veya siyah bir kapak
                pygame.draw.ellipse(screen, (20, 20, 20), 
                                   (center[0]-35, center[1]-10, 70, 20))
            else:
                # Göz Bebeği (Siyah ve hareketli)
                pupil_pos = (center[0] + self.pupil_offset[0], center[1] + self.pupil_offset[1])
                # Gözün ana siyahlığı
                pygame.draw.circle(screen, (10, 10, 10), pupil_pos, 35)
                # Işık parlaması (Canlılık verir)
                pygame.draw.circle(screen, (255, 255, 255), 
                                   (pupil_pos[0]-10, pupil_pos[1]-10), 8)
