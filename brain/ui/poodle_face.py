import pygame
import random
import sys

# Ekran Ayarları (Bizim 1024x600 DSI ekrana tam uyumlu)
WIDTH, HEIGHT = 1024, 600
FPS = 60

# Renkler
BLACK = (10, 10, 10)  # Derin siyah arka plan
EYE_COLOR = (20, 20, 20) # Gözlerin ana rengi (Poodle siyahı)
WHITE = (255, 255, 255) # Göz parlaması (Işık yansıması)

class PoodleFace:
    def __init__(self):
        self.eye_width = 120
        self.eye_height = 140
        self.left_eye_pos = [WIDTH // 2 - 180, HEIGHT // 2 - 50]
        self.right_eye_pos = [WIDTH // 2 + 180, HEIGHT // 2 - 50]
        self.nose_pos = [WIDTH // 2, HEIGHT // 2 + 80]
        
        self.is_blinking = False
        self.blink_speed = 0.2
        self.blink_status = 0 # 0: açık, 1: kapalı
        self.last_blink_time = pygame.time.get_ticks()
        self.next_blink_delay = random.randint(2000, 5000)

    def draw(self, screen):
        # Arka planı temizle
        screen.fill(BLACK)

        # Göz Kırpma Mantığı
        current_time = pygame.time.get_ticks()
        if current_time - self.last_blink_time > self.next_blink_delay:
            self.is_blinking = True
            
        if self.is_blinking:
            curr_height = 0 # Göz kapalıyken yükseklik 0
            if current_time - self.last_blink_time > self.next_blink_delay + 150:
                self.is_blinking = False
                self.last_blink_time = current_time
                self.next_blink_delay = random.randint(2000, 6000)
        else:
            curr_height = self.eye_height

        # Sol ve Sağ Gözü Çiz (Poodle'ın büyük yuvarlak gözleri)
        for pos in [self.left_eye_pos, self.right_eye_pos]:
            # Gözün ana siyahı
            pygame.draw.ellipse(screen, EYE_COLOR, (pos[0] - self.eye_width//2, pos[1] - curr_height//2, self.eye_width, curr_height))
            
            # Göz parlaması (Poodle'ın canlı bakışı için beyaz nokta)
            if not self.is_blinking:
                pygame.draw.circle(screen, WHITE, (pos[0] - 20, pos[1] - 30), 12)

        # Burun Çizimi (Görseldeki o sevimli siyah burun)
        pygame.draw.ellipse(screen, EYE_COLOR, (self.nose_pos[0] - 40, self.nose_pos[1] - 25, 80, 50))
        # Burun parlaması
        pygame.draw.ellipse(screen, (40, 40, 40), (self.nose_pos[0] - 25, self.nose_pos[1] - 15, 30, 15))

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Poodle Robot Face")
    clock = pygame.time.Clock()
    face = PoodleFace()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        face.draw(screen)
        pygame.display.flip()
        clock.tick(FPS)

if __name__ == "__main__":
    main()
