import math
import random
import time
from dataclasses import dataclass

import pygame


@dataclass
class RigState:
    body_y: float = 0.0
    head_y: float = 0.0
    head_rot: float = 0.0
    ear_left_rot: float = 0.0
    ear_right_rot: float = 0.0
    eye_open: float = 1.0
    gaze_x: float = 0.0
    gaze_y: float = 0.0
    mouth_open: float = 0.0


class PoodleCharacter:
    """
    Sprint 4.1:
    - state-independent canlılık
    - breathing
    - blinking
    - head bob
    - ear secondary motion
    - soft gaze drift

    Not:
    Bu sürüm pygame çizimleri ile çalışır.
    Sonraki aşamada katmanlı PNG asset sistemine geçirilebilir.
    """

    def __init__(self, width=1024, height=600):
        self.width = width
        self.height = height

        # --------------------------------------------------
        # Görsel tema
        # --------------------------------------------------
        self.bg_color = (245, 180, 210)
        self.bg_color_2 = (248, 205, 225)
        self.heart_color = (236, 146, 189)
        self.circle_color = (250, 220, 235)

        self.fur_color = (217, 212, 202)
        self.outline_color = (0, 0, 0)
        self.eye_color = (15, 15, 15)
        self.eye_highlight = (255, 255, 255)
        self.mouth_color = (25, 25, 25)
        self.cheek_color = (255, 170, 190)

        # --------------------------------------------------
        # Geometri
        # --------------------------------------------------
        self.center_x = width // 2
        self.center_y = height // 2 + 20

        self.body_center = (self.center_x - 120, self.center_y + 80)
        self.head_center = (self.center_x + 10, self.center_y - 40)

        self.body_size = (400, 360)
        self.head_size = (280, 270)

        self.ear_offset_left = (-95, -115)
        self.ear_offset_right = (95, -115)
        self.ear_size = (95, 95)

        self.eye_offset_left = (-45, -10)
        self.eye_offset_right = (45, -10)
        self.eye_size = (34, 64)

        self.mouth_offset = (0, 75)
        self.mouth_size = (62, 24)

        # --------------------------------------------------
        # Rig
        # --------------------------------------------------
        self.rig = RigState()

        # --------------------------------------------------
        # Animasyon parametreleri
        # --------------------------------------------------
        self.breath_speed = 1.25
        self.breath_amplitude = 3.0

        self.head_bob_speed = 1.35
        self.head_bob_amplitude = 2.0

        self.head_tilt_speed = 0.7
        self.head_tilt_amplitude = 2.2

        self.ear_follow_strength = 1.35
        self.ear_idle_flop_amplitude = 5.0

        self.gaze_strength_x = 10.0
        self.gaze_strength_y = 6.0

        self.micro_saccade_interval_min = 1.0
        self.micro_saccade_interval_max = 2.4

        self.blink_interval_min = 2.8
        self.blink_interval_max = 5.2
        self.blink_duration = 0.12

        self.start_time = time.time()

        self.is_blinking = False
        self.blink_started_at = 0.0
        self.next_blink_at = time.time() + random.uniform(
            self.blink_interval_min,
            self.blink_interval_max,
        )

        self.next_saccade_at = time.time() + random.uniform(
            self.micro_saccade_interval_min,
            self.micro_saccade_interval_max,
        )

        self.target_gaze_x = 0.0
        self.target_gaze_y = 0.0

        self.manual_gaze_enabled = False
        self.manual_gaze_target = (self.center_x, self.center_y)

        self.state = "idle"

    # ------------------------------------------------------
    # Public API
    # ------------------------------------------------------
    def set_state(self, state: str):
        self.state = state

    def update_gaze(self, x=None, y=None):
        if x is None or y is None:
            self.manual_gaze_enabled = False
            return

        self.manual_gaze_enabled = True
        self.manual_gaze_target = (x, y)

    def update(self, dt: float):
        now = time.time()
        t = now - self.start_time

        # 1) blink
        self._update_blink(now)

        # 2) gaze
        self._update_gaze(now)

        # 3) breathing
        self.rig.body_y = math.sin(t * self.breath_speed) * self.breath_amplitude

        # 4) head motion
        self.rig.head_y = math.sin(t * self.head_bob_speed) * self.head_bob_amplitude
        self.rig.head_rot = math.sin(t * self.head_tilt_speed) * self.head_tilt_amplitude

        # 5) ears follow head with extra softness
        self.rig.ear_left_rot = (
            self.rig.head_rot * self.ear_follow_strength
            + math.sin(t * 1.15 + 0.6) * self.ear_idle_flop_amplitude
        )
        self.rig.ear_right_rot = (
            self.rig.head_rot * self.ear_follow_strength
            - math.sin(t * 1.15 + 0.6) * self.ear_idle_flop_amplitude
        )

        # 6) eye openness from blink
        if self.is_blinking:
            blink_elapsed = now - self.blink_started_at
            progress = min(1.0, blink_elapsed / self.blink_duration)

            # hızlı kapan-aç
            if progress < 0.5:
                self.rig.eye_open = 1.0 - (progress / 0.5) * 0.92
            else:
                self.rig.eye_open = 0.08 + ((progress - 0.5) / 0.5) * 0.92
        else:
            self.rig.eye_open = 1.0

        # 7) mouth
        self.rig.mouth_open = 0.08 + abs(math.sin(t * 0.9)) * 0.04

        # 8) gaze easing
        self.rig.gaze_x += (self.target_gaze_x - self.rig.gaze_x) * 0.08
        self.rig.gaze_y += (self.target_gaze_y - self.rig.gaze_y) * 0.08

    def draw(self, screen: pygame.Surface):
        self._draw_background(screen)

        body_x = self.body_center[0]
        body_y = self.body_center[1] + self.rig.body_y

        head_x = self.head_center[0]
        head_y = self.head_center[1] + self.rig.body_y + self.rig.head_y

        # Body
        self._draw_body(screen, body_x, body_y)

        # Ears (behind head)
        self._draw_ear(
            screen,
            head_x + self.ear_offset_left[0],
            head_y + self.ear_offset_left[1],
            self.rig.ear_left_rot,
            left=True,
        )
        self._draw_ear(
            screen,
            head_x + self.ear_offset_right[0],
            head_y + self.ear_offset_right[1],
            self.rig.ear_right_rot,
            left=False,
        )

        # Head
        self._draw_head(screen, head_x, head_y)

        # Cheeks
        self._draw_cheeks(screen, head_x, head_y)

        # Eyes
        self._draw_eye(
            screen,
            head_x + self.eye_offset_left[0],
            head_y + self.eye_offset_left[1],
            self.rig.eye_open,
            self.rig.gaze_x,
            self.rig.gaze_y,
        )
        self._draw_eye(
            screen,
            head_x + self.eye_offset_right[0],
            head_y + self.eye_offset_right[1],
            self.rig.eye_open,
            self.rig.gaze_x,
            self.rig.gaze_y,
        )

        # Mouth
        self._draw_mouth(
            screen,
            head_x + self.mouth_offset[0],
            head_y + self.mouth_offset[1],
            self.rig.mouth_open,
        )

    # ------------------------------------------------------
    # Background
    # ------------------------------------------------------
    def _draw_background(self, screen: pygame.Surface):
        screen.fill(self.bg_color)

        # yumuşak daire
        pygame.draw.circle(
            screen,
            self.circle_color,
            (self.width // 2 + 40, self.height // 2 - 10),
            280,
        )

        # kalp pattern
        spacing = 48
        for y in range(20, self.height, spacing):
            for x in range(20, self.width, spacing):
                self._draw_heart(
                    screen,
                    x,
                    y,
                    self.heart_color,
                    scale=0.55,
                    alpha_like=((x + y) % 3),
                )

    def _draw_heart(self, screen, x, y, color, scale=1.0, alpha_like=0):
        # pseudo-alpha için tonu hafif değiştiriyoruz
        c = (
            min(255, color[0] + alpha_like * 7),
            min(255, color[1] + alpha_like * 7),
            min(255, color[2] + alpha_like * 7),
        )
        r = int(10 * scale)
        pygame.draw.circle(screen, c, (x - r, y), r)
        pygame.draw.circle(screen, c, (x + r, y), r)
        points = [(x - 2 * r, y), (x + 2 * r, y), (x, y + 3 * r)]
        pygame.draw.polygon(screen, c, points)

    # ------------------------------------------------------
    # Character primitives
    # ------------------------------------------------------
    def _draw_body(self, screen, cx, cy):
        w, h = self.body_size
        rect = pygame.Rect(int(cx - w / 2), int(cy - h / 2), w, h)
        pygame.draw.ellipse(screen, self.fur_color, rect)
        pygame.draw.ellipse(screen, self.outline_color, rect, 6)

        # dekoratif alt kıvrımlar
        for offset in (-80, -20, 40):
            pygame.draw.arc(
                screen,
                self.outline_color,
                pygame.Rect(int(cx + offset), int(cy + 50), 32, 42),
                0.2,
                3.2,
                5,
            )

    def _draw_head(self, screen, cx, cy):
        w, h = self.head_size
        rect = pygame.Rect(int(cx - w / 2), int(cy - h / 2), w, h)
        pygame.draw.ellipse(screen, self.fur_color, rect)
        pygame.draw.ellipse(screen, self.outline_color, rect, 6)

    def _draw_ear(self, screen, cx, cy, rotation_deg, left=True):
        w, h = self.ear_size
        ear_surface = pygame.Surface((w + 20, h + 20), pygame.SRCALPHA)

        rect = pygame.Rect(10, 10, w, h)
        pygame.draw.ellipse(ear_surface, self.fur_color, rect)
        pygame.draw.ellipse(ear_surface, self.outline_color, rect, 5)

        rotated = pygame.transform.rotate(ear_surface, rotation_deg)
        rrect = rotated.get_rect(center=(int(cx), int(cy)))
        screen.blit(rotated, rrect.topleft)

    def _draw_eye(self, screen, cx, cy, eye_open, gaze_x, gaze_y):
        eye_h = max(6, int(self.eye_size[1] * eye_open))
        eye_rect = pygame.Rect(
            int(cx - self.eye_size[0] / 2),
            int(cy - eye_h / 2),
            self.eye_size[0],
            eye_h,
        )

        pygame.draw.ellipse(screen, self.eye_color, eye_rect)

        # highlight sadece göz açıksa
        if eye_open > 0.25:
            hx = int(cx - 8 + gaze_x * 0.35)
            hy = int(cy - eye_h / 3 + gaze_y * 0.2)
            pygame.draw.ellipse(screen, self.eye_highlight, (hx, hy, 8, 10))

    def _draw_cheeks(self, screen, cx, cy):
        cheek_w, cheek_h = 34, 18
        left_rect = pygame.Rect(int(cx - 88), int(cy + 38), cheek_w, cheek_h)
        right_rect = pygame.Rect(int(cx + 54), int(cy + 38), cheek_w, cheek_h)
        pygame.draw.ellipse(screen, self.cheek_color, left_rect)
        pygame.draw.ellipse(screen, self.cheek_color, right_rect)

    def _draw_mouth(self, screen, cx, cy, mouth_open):
        width = 56
        height = max(8, int(self.mouth_size[1] + mouth_open * 18))

        mouth_rect = pygame.Rect(
            int(cx - width / 2),
            int(cy - height / 2),
            width,
            height,
        )

        pygame.draw.ellipse(screen, self.mouth_color, mouth_rect)

        # iç highlight çok hafif
        inner_w = max(10, width - 24)
        inner_h = max(4, height - 12)
        inner_rect = pygame.Rect(
            int(cx - inner_w / 2),
            int(cy - inner_h / 2 + 2),
            inner_w,
            inner_h,
        )
        pygame.draw.ellipse(screen, (70, 70, 70), inner_rect, 1)

    # ------------------------------------------------------
    # Animation internals
    # ------------------------------------------------------
    def _update_blink(self, now: float):
        if self.is_blinking:
            if now - self.blink_started_at >= self.blink_duration:
                self.is_blinking = False
                self.next_blink_at = now + random.uniform(
                    self.blink_interval_min,
                    self.blink_interval_max,
                )
        else:
            if now >= self.next_blink_at:
                self.is_blinking = True
                self.blink_started_at = now

    def _update_gaze(self, now: float):
        if self.manual_gaze_enabled:
            mx, my = self.manual_gaze_target
            dx = (mx - self.width / 2) / (self.width / 2)
            dy = (my - self.height / 2) / (self.height / 2)
            self.target_gaze_x = dx * self.gaze_strength_x
            self.target_gaze_y = dy * self.gaze_strength_y
            return

        if now >= self.next_saccade_at:
            self.target_gaze_x = random.uniform(-self.gaze_strength_x * 0.4, self.gaze_strength_x * 0.4)
            self.target_gaze_y = random.uniform(-self.gaze_strength_y * 0.35, self.gaze_strength_y * 0.35)
            self.next_saccade_at = now + random.uniform(
                self.micro_saccade_interval_min,
                self.micro_saccade_interval_max,
            )
