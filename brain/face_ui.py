import pygame
import random
import math


class PoodleFace:
    def __init__(self, width=1024, height=600):
        self.width = width
        self.height = height

        # --- RENK PALETİ ---
        self.COLOR_BG = (8, 8, 12)
        self.COLOR_BG_2 = (18, 18, 28)
        self.COLOR_FUR = (245, 235, 215)
        self.COLOR_FUR_SHADOW = (225, 215, 195)
        self.COLOR_EYE_OUT = (28, 28, 32)
        self.COLOR_PUPIL = (0, 0, 0)
        self.COLOR_NOSE = (20, 20, 20)
        self.COLOR_GLINT = (255, 255, 255)
        self.COLOR_MOUTH = (50, 10, 15)
        self.COLOR_TONGUE = (255, 110, 130)
        self.COLOR_CHEEK = (255, 170, 180)

        # --- ANA POZİSYONLAR ---
        self.base_center_x = width // 2
        self.base_center_y = height // 2 - 10

        self.eye_offset_x = 145
        self.eye_offset_y = -35
        self.ear_offset_x = 310
        self.nose_offset_y = 92
        self.mouth_offset_y = 150

        self.pupil_offset = [0, 0]
        self.target_gaze = [0, 0]
        self.current_gaze = [0.0, 0.0]

        # Animasyon zamanlayıcıları
        self.start_time = pygame.time.get_ticks()

        # Göz kırpma
        self.is_blinking = False
        self.blink_progress = 0.0
        self.last_blink = pygame.time.get_ticks()
        self.next_blink_time = random.randint(1800, 4500)
        self.double_blink_chance = 0.28
        self.pending_second_blink = False

        # Konuşma / ağız hareketi
        self.talking = True
        self.talk_phase = 0.0

        # Rastgele bakış değişimi
        self.last_gaze_change = pygame.time.get_ticks()
        self.next_gaze_change = random.randint(900, 2200)

        # Parçacıklar
        self.particles = []
        for _ in range(34):
            self.particles.append({
                "x": random.randint(0, self.width),
                "y": random.randint(0, self.height),
                "r": random.randint(2, 6),
                "speed": random.uniform(0.15, 0.65),
                "alpha": random.randint(35, 100),
                "phase": random.uniform(0, math.pi * 2)
            })

    def update_gaze(self, target_x=None, target_y=None):
        """
        Kameradan gelen koordinat varsa ona bakar.
        Yoksa kendi içinde rastgele bakış üretir.
        """
        now = pygame.time.get_ticks()

        if target_x is not None and target_y is not None:
            dx = (target_x - 320) / 12
            dy = (target_y - 240) / 12
            self.target_gaze[0] = max(-28, min(28, dx))
            self.target_gaze[1] = max(-16, min(16, dy))
        else:
            if now - self.last_gaze_change > self.next_gaze_change:
                self.last_gaze_change = now
                self.next_gaze_change = random.randint(900, 2200)
                self.target_gaze[0] = random.randint(-22, 22)
                self.target_gaze[1] = random.randint(-10, 12)

        # Yumuşak geçiş
        self.current_gaze[0] += (self.target_gaze[0] - self.current_gaze[0]) * 0.08
        self.current_gaze[1] += (self.target_gaze[1] - self.current_gaze[1]) * 0.08

        # Mikro hareket
        t = (pygame.time.get_ticks() - self.start_time) / 1000.0
        micro_x = math.sin(t * 3.2) * 1.4
        micro_y = math.cos(t * 2.7) * 0.8

        self.pupil_offset[0] = self.current_gaze[0] + micro_x
        self.pupil_offset[1] = self.current_gaze[1] + micro_y

    def _update_blink(self):
        now = pygame.time.get_ticks()

        if not self.is_blinking and (now - self.last_blink > self.next_blink_time):
            self.is_blinking = True
            self.blink_progress = 0.0

        if self.is_blinking:
            self.blink_progress += 0.22
            if self.blink_progress >= 2.0:
                self.is_blinking = False
                self.blink_progress = 0.0
                self.last_blink = now

                if self.pending_second_blink:
                    self.pending_second_blink = False
                    self.next_blink_time = 140
                else:
                    if random.random() < self.double_blink_chance:
                        self.pending_second_blink = True
                        self.next_blink_time = 120
                    else:
                        self.next_blink_time = random.randint(1800, 4500)

    def _blink_ratio(self):
        """
        1.0 = açık göz
        0.0 = kapalı göz
        """
        if not self.is_blinking:
            return 1.0

        if self.blink_progress < 1.0:
            return max(0.0, 1.0 - self.blink_progress)
        return min(1.0, self.blink_progress - 1.0)

    def _draw_vertical_gradient(self, screen):
        for y in range(self.height):
            ratio = y / self.height
            r = int(self.COLOR_BG[0] * (1 - ratio) + self.COLOR_BG_2[0] * ratio)
            g = int(self.COLOR_BG[1] * (1 - ratio) + self.COLOR_BG_2[1] * ratio)
            b = int(self.COLOR_BG[2] * (1 - ratio) + self.COLOR_BG_2[2] * ratio)
            pygame.draw.line(screen, (r, g, b), (0, y), (self.width, y))

    def _draw_particles(self, screen, t):
        particle_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)

        for p in self.particles:
            yy = p["y"] + math.sin(t * p["speed"] + p["phase"]) * 14
            xx = p["x"] + math.cos(t * p["speed"] * 0.7 + p["phase"]) * 8
            alpha = int(p["alpha"] + math.sin(t * 2 + p["phase"]) * 20)
            alpha = max(15, min(130, alpha))
            pygame.draw.circle(
                particle_surface,
                (255, 255, 255, alpha),
                (int(xx), int(yy)),
                p["r"]
            )

        screen.blit(particle_surface, (0, 0))

    def _draw_fluffy_ear(self, screen, x, y, wobble=0):
        # Kulağı birkaç üst üste daire ile çiz
        circles = [
            (0, 0, 56),
            (-8, 26, 49),
            (8, 50, 43),
            (0, 74, 37)
        ]
        for dx, dy, rr in circles:
            pygame.draw.circle(screen, self.COLOR_FUR_SHADOW, (int(x + dx + wobble * 0.5), int(y + dy + 6)), rr)
            pygame.draw.circle(screen, self.COLOR_FUR, (int(x + dx + wobble), int(y + dy)), rr)

    def _draw_main_face(self, screen, cx, cy, breath_scale):
        face_r = int(238 * breath_scale)
        pygame.draw.circle(screen, self.COLOR_FUR_SHADOW, (cx, cy + 10), face_r + 4)
        pygame.draw.circle(screen, self.COLOR_FUR, (cx, cy), face_r)

        # Üstte hafif parlama
        highlight = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        pygame.draw.ellipse(
            highlight,
            (255, 255, 255, 30),
            (cx - 120, cy - 190, 240, 90)
        )
        screen.blit(highlight, (0, 0))

    def draw(self, screen):
        now = pygame.time.get_ticks()
        t = (now - self.start_time) / 1000.0

        self.update_gaze()
        self._update_blink()

        blink_ratio = self._blink_ratio()

        # Hareket parametreleri
        bob_y = math.sin(t * 1.8) * 6
        bob_x = math.sin(t * 1.1) * 3
        breath_scale = 1.0 + math.sin(t * 2.2) * 0.012
        ear_wobble = math.sin(t * 2.4) * 7
        cheek_pulse = (math.sin(t * 4.0) + 1) * 0.5
        nose_glow = (math.sin(t * 5.2) + 1) * 0.5

        cx = int(self.base_center_x + bob_x)
        cy = int(self.base_center_y + bob_y)

        # Konuşma animasyonu
        if self.talking:
            self.talk_phase += 0.20
        mouth_open = 12 + (math.sin(self.talk_phase) + 1) * 9

        # 1. Arkaplan
        self._draw_vertical_gradient(screen)
        self._draw_particles(screen, t)

        # 2. Kulaklar
        self._draw_fluffy_ear(screen, cx - self.ear_offset_x, cy - 78, -ear_wobble)
        self._draw_fluffy_ear(screen, cx + self.ear_offset_x, cy - 78, ear_wobble)

        # 3. Ana yüz
        self._draw_main_face(screen, cx, cy, breath_scale)

        # 4. Yanaklar
        blush_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        cheek_alpha = int(45 + cheek_pulse * 35)
        pygame.draw.circle(
            blush_surface,
            (*self.COLOR_CHEEK, cheek_alpha),
            (cx - 120, cy + 75),
            42
        )
        pygame.draw.circle(
            blush_surface,
            (*self.COLOR_CHEEK, cheek_alpha),
            (cx + 120, cy + 75),
            42
        )
        screen.blit(blush_surface, (0, 0))

        # 5. Gözler
        for side in (-1, 1):
            eye_x = cx + self.eye_offset_x * side
            eye_y = cy + self.eye_offset_y

            # Dış halka
            pygame.draw.circle(screen, self.COLOR_EYE_OUT, (eye_x, eye_y), 74)

            if blink_ratio < 0.15:
                pygame.draw.line(
                    screen,
                    self.COLOR_PUPIL,
                    (eye_x - 44, eye_y),
                    (eye_x + 44, eye_y),
                    8
                )
            else:
                eye_white_h = max(12, int(118 * blink_ratio))
                eye_white_rect = pygame.Rect(eye_x - 54, eye_y - eye_white_h // 2, 108, eye_white_h)
                pygame.draw.ellipse(screen, (250, 250, 250), eye_white_rect)

                pupil_x = int(eye_x + self.pupil_offset[0])
                pupil_y = int(eye_y + self.pupil_offset[1] * blink_ratio)

                pupil_r = max(16, int(34 + (1 - blink_ratio) * -8))
                pygame.draw.circle(screen, self.COLOR_PUPIL, (pupil_x, pupil_y), pupil_r)

                # İç yansıma
                pygame.draw.circle(screen, (255, 255, 255), (pupil_x - 10, pupil_y - 10), 10)
                pygame.draw.circle(screen, (180, 220, 255), (pupil_x + 10, pupil_y + 7), 4)

        # 6. Burun
        nose_rect = pygame.Rect(cx - 45, cy + self.nose_offset_y, 90, 56)
        pygame.draw.ellipse(screen, self.COLOR_NOSE, nose_rect)

        nose_highlight = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        pygame.draw.ellipse(
            nose_highlight,
            (255, 255, 255, int(40 + nose_glow * 45)),
            (cx - 18, cy + self.nose_offset_y + 10, 28, 15)
        )
        screen.blit(nose_highlight, (0, 0))

        # 7. Ağız
        mouth_w = 88
        mouth_h = int(mouth_open)
        mouth_rect = pygame.Rect(cx - mouth_w // 2, cy + self.mouth_offset_y, mouth_w, mouth_h + 18)
        pygame.draw.ellipse(screen, self.COLOR_MOUTH, mouth_rect)

        # Dil
        tongue_rect = pygame.Rect(cx - 18, cy + self.mouth_offset_y + 14, 36, max(8, mouth_h // 2 + 2))
        pygame.draw.ellipse(screen, self.COLOR_TONGUE, tongue_rect)

        # 8. Minik kaş / göz üstü vurgu
        pygame.draw.arc(screen, (80, 80, 90), (cx - 205, cy - 105, 110, 50), math.radians(200), math.radians(340), 3)
        pygame.draw.arc(screen, (80, 80, 90), (cx + 95, cy - 105, 110, 50), math.radians(200), math.radians(340), 3)


def main():
    pygame.init()
    screen = pygame.display.set_mode((1024, 600))
    pygame.display.set_caption("Poodle Robot Simülasyonu - Canlı Versiyon")
    clock = pygame.time.Clock()

    face = PoodleFace(1024, 600)

    running = True
    while running:
        mouse_x, mouse_y = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            # SPACE ile konuşma animasyonunu aç/kapat
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    face.talking = not face.talking

        # İstersen fareyi takip ettir:
        face.update_gaze(mouse_x, mouse_y)

        face.draw(screen)

        # Alt bilgi
        font = pygame.font.SysFont("Arial", 18)
        info = font.render("SPACE: ağız animasyonu aç/kapat", True, (170, 170, 170))
        screen.blit(info, (20, 20))

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    main()
