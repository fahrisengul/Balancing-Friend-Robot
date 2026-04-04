import pygame
import random
import os
import math

class PoodleFace:
    """
    poddle_v3.png için Anchor-based facial rig yapısı.
    Tüm yüz bileşenleri (gözler, ağız) sabit semantik çapalar üzerinden yönetilir.
    """

    def __init__(self, width=1024, height=600):
        self.width = width
        self.height = height

        current_dir = os.path.dirname(os.path.abspath(__file__))
        bg_path = os.path.join(current_dir, "poddle_v3.png")

        try:
            self.bg_image = pygame.image.load(bg_path).convert()
            self.bg_image = pygame.transform.scale(self.bg_image, (self.width, self.height))
            self.has_bg = True
            print(">>> [V10 - ANCHOR BASED FACE RIG] AKTIF <<<")
        except Exception as e:
            self.has_bg = False
            self.bg_image = None
            print(f"Arka plan yuklenemedi: {e}")

        # ------------------------------------------------------------------
        # FACE RIG CONFIGURATION
        # Görsel üzerindeki hassas koordinatlar ve boyutlar
        # ------------------------------------------------------------------
        self.FACE_RIG = {
            "head_center": (515, 265),

            # Gözler: 70x140 boyutunda, halkalara tam oturan koordinatlar
            "eye_left_center": (404, 290),
            "eye_right_center": (626, 290),
            "eye_width": 70,
            "eye_height": 140,

            # Ağız çapası
            "mouth_center": (515, 355),
            "mouth_width": 56,
            "mouth_height": 26,

            # Siyah göz içindeki beyaz parlama (Glint) ayarları
            "glint_dx": -10,
            "glint_dy": -36,
            "glint_w": 12,
            "glint_h": 10,
        }

        # Renk Paleti
        self.EYE_COLOR = (10, 10, 10)
        self.PUPIL_COLOR = (255, 255, 255)
        self.MOUTH_COLOR = (10, 10, 10)
        self.GUIDE_COLOR = (0, 255, 180)

        # Durum Yönetimi
        self.state = "idle"
        self.talking = False

        # Göz Animasyon Parametreleri
        self.eye_scale_y = 1.0
        self.target_scale_y = 1.0
        self.last_blink = pygame.time.get_ticks()
        self.next_blink_ms = random.randint(2800, 5200)

        # Ağız Animasyon Parametreleri
        self.mouth_open = 0.0
        self.mouth_target = 0.0
        self.talk_phase = 0.0

        # Bakış (Gaze) Takibi
        self.target_pos = [0.0, 0.0]
        self.current_pos = [0.0, 0.0]

        # Debug Modu
        self.show_guides = False

    def set_state(self, state):
        """Robotun moduna göre göz ve ağız hedeflerini belirler."""
        self.state = state
        self.talking = (state == "speaking")

        if state == "listening":
            self.target_scale_y = 1.15
            self.mouth_target = 0.08
        elif state == "speaking":
            self.target_scale_y = 0.95
            # Konuşma animasyonu _update_mouth içinde dinamik hesaplanır
        else:
            self.target_scale_y = 1.0
            self.mouth_target = 0.0

    def update_gaze(self, tx=None, ty=None):
        """Kamera veya Mouse koordinatlarına göre bakışı yumuşatarak günceller."""
        if tx is not None and ty is not None:
            # Gözlerin yuvadan taşmaması için kısıtlı hareket alanı (Clamping)
            gx = (tx - self.width // 2) / 140.0
            gy = (ty - self.height // 2) / 170.0
            self.target_pos = [
                max(-6, min(6, gx)),
                max(-8, min(8, gy)),
            ]
        else:
            self.target_pos = [0.0, 0.0]

        # Yumuşak Takip (LERP)
        self.current_pos[0] += (self.target_pos[0] - self.current_pos[0]) * 0.10
        self.current_pos[1] += (self.target_pos[1] - self.current_pos[1]) * 0.10

    def _update_blink(self):
        """Rastgele aralıklarla göz kırpma işlemini yönetir."""
        now = pygame.time.get_ticks()
        if now - self.last_blink > self.next_blink_ms:
            self.eye_scale_y = 0.05
            if now - self.last_blink > self.next_blink_ms + 140:
                self.last_blink = now
                self.next_blink_ms = random.randint(2800, 5200)

    def _update_mouth(self):
        """Konuşma ve Dinleme modlarına göre ağız formunu günceller."""
        if self.state == "speaking":
            self.talk_phase += 0.23
            self.mouth_target = 0.35 + abs(math.sin(self.talk_phase * 1.3)) * 0.95
        elif self.state == "listening":
            self.mouth_target = 0.08
        else:
            self.mouth_target = 0.0

        self.mouth_open += (self.mouth_target - self.mouth_open) * 0.18

    def _draw_eye(self, screen, cx, cy):
        """Tek bir gözü ve parlama noktasını çizer."""
        w = self.FACE_RIG["eye_width"]
        h = max(2, self.FACE_RIG["eye_height"] * self.eye_scale_y)

        gx = self.current_pos[0]
        gy = self.current_pos[1]

        # Siyah Göz
        pygame.draw.ellipse(
            screen,
            self.EYE_COLOR,
            (cx - w // 2 + gx, cy - h // 2 + gy, w, h),
        )

        # Parlama (Sadece gözler yeterince açıkken)
        if self.eye_scale_y > 0.35:
            pygame.draw.ellipse(
                screen,
                self.PUPIL_COLOR,
                (
                    cx + self.FACE_RIG["glint_dx"] + gx,
                    cy + self.FACE_RIG["glint_dy"] + gy,
                    self.FACE_RIG["glint_w"],
                    self.FACE_RIG["glint_h"],
                ),
            )

    def _draw_mouth(self, screen):
        """Ağız formunu duruma göre (çizgi veya oval) çizer."""
        mx, my = self.FACE_RIG["mouth_center"]
        base_w = self.FACE_RIG["mouth_width"]
        base_h = self.FACE_RIG["mouth_height"]

        if self.mouth_open < 0.12:
            # Kapalı ağız / Dinleme: İnce düz çizgi
            pygame.draw.line(screen, self.MOUTH_COLOR, (mx - 9, my), (mx + 9, my), 3)
        else:
            # Konuşma: Dinamik oval
            h = int(base_h + self.mouth_open * 22)
            w = int(base_w - self.mouth_open * 8)
            pygame.draw.ellipse(screen, self.MOUTH_COLOR, (mx - w // 2, my - h // 2, w, h))

    def _draw_guides(self, screen):
        """Geliştirme için rehber çizgileri çizer (G tuşuyla aktif olur)."""
        if not self.show_guides:
            return
        font = pygame.font.SysFont("Arial", 14)
        for label, (cx, cy) in {
            "L-EYE": self.FACE_RIG["eye_left_center"],
            "R-EYE": self.FACE_RIG["eye_right_center"],
            "MOUTH": self.FACE_RIG["mouth_center"],
            "HEAD": self.FACE_RIG["head_center"],
        }.items():
            pygame.draw.line(screen, self.GUIDE_COLOR, (cx - 12, cy), (cx + 12, cy), 1)
            pygame.draw.line(screen, self.GUIDE_COLOR, (cx, cy - 12), (cx, cy + 12), 1)
            txt = font.render(f"{label} ({cx},{cy})", True, self.GUIDE_COLOR)
            screen.blit(txt, (cx + 8, cy - 18))

    def draw(self, screen):
        """Tüm yüzü ekrana çizer."""
        if self.has_bg:
            screen.blit(self.bg_image, (0, 0))
        else:
            screen.fill((30, 30, 30))

        # Animasyon güncellemeleri
        self.eye_scale_y += (self.target_scale_y - self.eye_scale_y) * 0.10
        self._update_blink()
        self._update_mouth()

        # Bileşenleri çiz
        self._draw_eye(screen, *self.FACE_RIG["eye_left_center"])
        self._draw_eye(screen, *self.FACE_RIG["eye_right_center"])
        self._draw_mouth(screen)
        self._draw_guides(screen)

    # main.py ile uyumluluk için (eskiden kalan fonksiyonları destekler)
    def handle_calibration(self, key):
        pass
