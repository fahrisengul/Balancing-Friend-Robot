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
    cheek_alpha: float = 0.0


class PoodleCharacter:
    """
    Sprint 4.1 v2
    - state-aware 2D character rig
    - breathing
    - blinking
    - head bob
    - ear secondary motion
    - gaze drift / manual gaze
    - speaking/listening/thinking/muted visual separation
    """

    VALID_STATES = {
        "idle",
        "attentive",
        "listening",
        "thinking",
        "speaking",
        "muted",
        "error",
    }

    def __init__(self, width=1024, height=600):
        self.width = width
        self.height = height

        # --------------------------------------------------
        # Colors
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
        self.error_color = (255, 140, 90)
        self.hud_color = (255, 255, 255)

        # --------------------------------------------------
        # Geometry
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
        # State / Rig
        # --------------------------------------------------
        self.state = "idle"
        self.state_entered_at = time.time()
        self.rig = RigState()

        # --------------------------------------------------
        # Animation base params
        # --------------------------------------------------
        self.start_time = time.time()

        self.blink_interval_min = 2.8
        self.blink_interval_max = 5.2
        self.blink_duration = 0.12

        self.is_blinking = False
        self.blink_started_at = 0.0
        self.next_blink_at = time.time() + random.uniform(
            self.blink_interval_min,
            self.blink_interval_max,
        )

        self.micro_saccade_interval_min = 1.0
        self.micro_saccade_interval_max = 2.4
        self.next_saccade_at = time.time() + random.uniform(
            self.micro_saccade_interval_min,
            self.micro_saccade_interval_max,
        )

        self.manual_gaze_enabled = False
        self.manual_gaze_target = (self.center_x, self.center_y)
        self.target_gaze_x = 0.0
        self.target_gaze_y = 0.0

        pygame.font.init()
        self.hud_font = pygame.font.SysFont("Arial", 18, bold=True)

    # ------------------------------------------------------
    # Public API
    # ------------------------------------------------------
    def set_state(self, state: str):
        if state not in self.VALID_STATES:
            state = "idle"

        if state == self.state:
            return

        self.state = state
        self.state_entered_at = time.time()

        # state değişiminde blink/gaze ritmini hafif resetle
        now = time.time()
        self.next_blink_at = now + random.uniform(
            self.blink_interval_min,
            self.blink_interval_max,
        )
        self.next_saccade_at = now + random.uniform(
            self.micro_saccade_interval_min,
            self.micro_saccade_interval_max,
        )

    def update_gaze(self, x=None, y=None):
        if x is None or y is None:
            self.manual_gaze_enabled = False
            return

        self.manual_gaze_enabled = True
        self.manual_gaze_target = (x, y)

    def update(self, dt: float):
        now = time.time()
        t = now - self.start_time

        params = self._get_state_params(self.state)

        self._update_blink(now, params)
        self._update_gaze(now, params)

        # body / head
        self.rig.body_y = math.sin(t * params["breath_speed"]) * params["breath_amplitude"]
        self.rig.head_y = math.sin(t * params["head_bob_speed"]) * params["head_bob_amplitude"]
        self.rig.head_rot = math.sin(t * params["head_tilt_speed"]) * params["head_tilt_amplitude"]

        # ears
        self.rig.ear_left_rot = (
            self.rig.head_rot * params["ear_follow_strength"]
            + math.sin(t * 1.15 + 0.6) * params["ear_idle_flop_amplitude"]
            + params["ear_lift_bias_left"]
        )
        self.rig.ear_right_rot = (
            self.rig.head_rot * params["ear_follow_strength"]
            - math.sin(t * 1.15 + 0.6) * params["ear_idle_flop_amplitude"]
            + params["ear_lift_bias_right"]
        )

        # eye openness
        target_eye_open = params["eye_open_ratio"]

        if self.is_blinking:
            blink_elapsed = now - self.blink_started_at
            progress = min(1.0, blink_elapsed / self.blink_duration)

            if progress < 0.5:
                blink_value = target_eye_open - (progress / 0.5) * (target_eye_open - 0.08)
            else:
                blink_value = 0.08 + ((progress - 0.5) / 0.5) * (target_eye_open - 0.08)

            self.rig.eye_open = blink_value
        else:
            self.rig.eye_open += (target_eye_open - self.rig.eye_open) * 0.12

        # mouth
        if self.state == "speaking":
            self.rig.mouth_open = 0.18 + abs(math.sin(t * 8.5)) * 0.42
        elif self.state == "muted":
            self.rig.mouth_open = 0.0
        elif self.state == "thinking":
            self.rig.mouth_open += (0.03 - self.rig.mouth_open) * 0.15
        else:
            self.rig.mouth_open += (0.06 - self.rig.mouth_open) * 0.12

        # cheeks
        self.rig.cheek_alpha += (params["cheek_alpha"] - self.rig.cheek_alpha) * 0.08

        # gaze easing
        self.rig.gaze_x += (self.target_gaze_x - self.rig.gaze_x) * params["gaze_ease"]
        self.rig.gaze_y += (self.target_gaze_y - self.rig.gaze_y) * params["gaze_ease"]

    def draw(self, screen: pygame.Surface):
        params = self._get_state_params(self.state)

        self._draw_background(screen)

        body_x = self.body_center[0]
        body_y = self.body_center[1] + self.rig.body_y

        head_x = self.head_center[0]
        head_y = self.head_center[1] + self.rig.body_y + self.rig.head_y

        self._draw_body(screen, body_x, body_y)

        self._draw_ear(
            screen,
            head_x + self.ear_offset_left[0],
            head_y + self.ear_offset_left[1],
            self.rig.ear_left_rot,
        )
        self._draw_ear(
            screen,
            head_x + self.ear_offset_right[0],
            head_y + self.ear_offset_right[1],
            self.rig.ear_right_rot,
        )

        self._draw_head(screen, head_x, head_y)

        if self.rig.cheek_alpha > 0.05:
            self._draw_cheeks(screen, head_x, head_y, self.rig.cheek_alpha)

        self._draw_eye(
            screen,
            head_x + self.eye_offset_left[0],
            head_y + self.eye_offset_left[1],
            self.rig.eye_open,
            self.rig.gaze_x,
            self.rig.gaze_y,
            params,
        )
        self._draw_eye(
            screen,
            head_x + self.eye_offset_right[0],
            head_y + self.eye_offset_right[1],
            self.rig.eye_open,
            self.rig.gaze_x,
            self.rig.gaze_y,
            params,
        )

        self._draw_mouth(
            screen,
            head_x + self.mouth_offset[0],
            head_y + self.mouth_offset[1],
            self.rig.mouth_open,
            params,
        )

        self._draw_hud(screen, params)

    # ------------------------------------------------------
    # State params
    # ------------------------------------------------------
    def _get_state_params(self, state: str):
        base = {
            "breath_speed": 1.25,
            "breath_amplitude": 3.0,
            "head_bob_speed": 1.35,
            "head_bob_amplitude": 2.0,
            "head_tilt_speed": 0.7,
            "head_tilt_amplitude": 2.2,
            "ear_follow_strength": 1.35,
            "ear_idle_flop_amplitude": 5.0,
            "ear_lift_bias_left": 0.0,
            "ear_lift_bias_right": 0.0,
            "eye_open_ratio": 1.0,
            "gaze_strength_x": 10.0,
            "gaze_strength_y": 6.0,
            "gaze_ease": 0.08,
            "cheek_alpha": 0.0,
            "hud_label": None,
            "error_mode": False,
        }

        if state == "idle":
            return base

        if state == "attentive":
            base.update({
                "head_bob_amplitude": 1.2,
                "head_tilt_amplitude": 1.5,
                "ear_lift_bias_left": -6.0,
                "ear_lift_bias_right": 6.0,
                "eye_open_ratio": 1.05,
                "gaze_strength_x": 14.0,
                "gaze_strength_y": 8.0,
                "cheek_alpha": 0.15,
                "hud_label": "ATTENTIVE",
            })
            return base

        if state == "listening":
            base.update({
                "head_bob_amplitude": 0.8,
                "head_tilt_amplitude": 1.3,
                "ear_lift_bias_left": -4.0,
                "ear_lift_bias_right": 4.0,
                "eye_open_ratio": 1.08,
                "gaze_strength_x": 16.0,
                "gaze_strength_y": 9.0,
                "cheek_alpha": 0.18,
                "hud_label": "LISTENING",
            })
            return base

        if state == "thinking":
            base.update({
                "breath_speed": 1.0,
                "head_bob_amplitude": 0.6,
                "head_tilt_amplitude": 3.0,
                "ear_idle_flop_amplitude": 2.0,
                "eye_open_ratio": 0.76,
                "gaze_strength_x": 7.0,
                "gaze_strength_y": 4.0,
                "gaze_ease": 0.05,
                "hud_label": "THINKING",
            })
            return base

        if state == "speaking":
            base.update({
                "head_bob_speed": 2.6,
                "head_bob_amplitude": 2.8,
                "head_tilt_amplitude": 1.6,
                "ear_idle_flop_amplitude": 6.0,
                "eye_open_ratio": 0.95,
                "cheek_alpha": 0.22,
                "hud_label": "SPEAKING",
            })
            return base

        if state == "muted":
            base.update({
                "breath_speed": 0.85,
                "head_bob_amplitude": 0.5,
                "head_tilt_amplitude": 0.8,
                "ear_idle_flop_amplitude": 1.5,
                "eye_open_ratio": 0.42,
                "gaze_strength_x": 4.0,
                "gaze_strength_y": 2.0,
                "gaze_ease": 0.04,
                "hud_label": "MUTED",
            })
            return base

        if state == "error":
            base.update({
                "breath_speed": 1.8,
                "head_bob_amplitude": 1.0,
                "head_tilt_amplitude": 4.0,
                "eye_open_ratio": 0.58,
                "gaze_strength_x": 5.0,
                "gaze_strength_y": 3.0,
                "hud_label": "ERROR",
                "error_mode": True,
            })
            return base

        return base

    # ------------------------------------------------------
    # Background
    # ------------------------------------------------------
    def _draw_background(self, screen: pygame.Surface):
        screen.fill(self.bg_color)

        pygame.draw.circle(
            screen,
            self.circle_color,
            (self.width // 2 + 40, self.height // 2 - 10),
            280,
        )

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
        w, h = 400, 360
        rect = pygame.Rect(int(cx - w / 2), int(cy - h / 2), w, h)
        pygame.draw.ellipse(screen, self.fur_color, rect)
        pygame.draw.ellipse(screen, self.outline_color, rect, 6)

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
        w, h = 280, 270
        rect = pygame.Rect(int(cx - w / 2), int(cy - h / 2), w, h)
        pygame.draw.ellipse(screen, self.fur_color, rect)
        pygame.draw.ellipse(screen, self.outline_color, rect, 6)

    def _draw_ear(self, screen, cx, cy, rotation_deg):
        w, h = 95, 95
        ear_surface = pygame.Surface((w + 20, h + 20), pygame.SRCALPHA)

        rect = pygame.Rect(10, 10, w, h)
        pygame.draw.ellipse(ear_surface, self.fur_color, rect)
        pygame.draw.ellipse(ear_surface, self.outline_color, rect, 5)

        rotated = pygame.transform.rotate(ear_surface, rotation_deg)
        rrect = rotated.get_rect(center=(int(cx), int(cy)))
        screen.blit(rotated, rrect.topleft)

    def _draw_eye(self, screen, cx, cy, eye_open, gaze_x, gaze_y, params):
        eye_h = max(6, int(64 * eye_open))
        eye_rect = pygame.Rect(
            int(cx - 17),
            int(cy - eye_h / 2),
            34,
            eye_h,
        )

        eye_color = self.error_color if params["error_mode"] else self.eye_color
        pygame.draw.ellipse(screen, eye_color, eye_rect)

        if eye_open > 0.25:
            hx = int(cx - 8 + gaze_x * 0.35)
            hy = int(cy - eye_h / 3 + gaze_y * 0.2)
            pygame.draw.ellipse(screen, self.eye_highlight, (hx, hy, 8, 10))

    def _draw_cheeks(self, screen, cx, cy, alpha_level):
        cheek_w, cheek_h = 34, 18

        cheek_surface = pygame.Surface((140, 40), pygame.SRCALPHA)
        alpha = max(0, min(255, int(alpha_level * 255)))

        cheek_color = (*self.cheek_color, alpha)
        pygame.draw.ellipse(cheek_surface, cheek_color, (0, 10, cheek_w, cheek_h))
        pygame.draw.ellipse(cheek_surface, cheek_color, (88, 10, cheek_w, cheek_h))

        screen.blit(cheek_surface, (int(cx - 70), int(cy + 28)))

    def _draw_mouth(self, screen, cx, cy, mouth_open, params):
        if self.state == "muted":
            pygame.draw.line(
                screen,
                self.mouth_color,
                (int(cx - 22), int(cy)),
                (int(cx + 22), int(cy)),
                4,
            )
            return

        if self.state == "thinking":
            pygame.draw.arc(
                screen,
                self.mouth_color,
                pygame.Rect(int(cx - 20), int(cy - 4), 40, 18),
                0.3,
                2.85,
                3,
            )
            return

        width = 56
        height = max(8, int(self.mouth_size[1] + mouth_open * 18))

        mouth_rect = pygame.Rect(
            int(cx - width / 2),
            int(cy - height / 2),
            width,
            height,
        )
        mouth_color = self.error_color if params["error_mode"] else self.mouth_color
        pygame.draw.ellipse(screen, mouth_color, mouth_rect)

        inner_w = max(10, width - 24)
        inner_h = max(4, height - 12)
        inner_rect = pygame.Rect(
            int(cx - inner_w / 2),
            int(cy - inner_h / 2 + 2),
            inner_w,
            inner_h,
        )
        pygame.draw.ellipse(screen, (70, 70, 70), inner_rect, 1)

    def _draw_hud(self, screen, params):
        label = params.get("hud_label")
        if not label:
            return

        surf = self.hud_font.render(label, True, self.hud_color)
        screen.blit(surf, (24, 20))

    # ------------------------------------------------------
    # Animation internals
    # ------------------------------------------------------
    def _update_blink(self, now: float, params):
        if self.state == "speaking":
            # konuşurken daha az blink
            blink_min = 4.0
            blink_max = 6.0
        elif self.state == "muted":
            blink_min = 3.5
            blink_max = 6.5
        else:
            blink_min = self.blink_interval_min
            blink_max = self.blink_interval_max

        if self.is_blinking:
            if now - self.blink_started_at >= self.blink_duration:
                self.is_blinking = False
                self.next_blink_at = now + random.uniform(blink_min, blink_max)
        else:
            if now >= self.next_blink_at:
                self.is_blinking = True
                self.blink_started_at = now

    def _update_gaze(self, now: float, params):
        if self.manual_gaze_enabled:
            mx, my = self.manual_gaze_target
            dx = (mx - self.width / 2) / (self.width / 2)
            dy = (my - self.height / 2) / (self.height / 2)
            self.target_gaze_x = dx * params["gaze_strength_x"]
            self.target_gaze_y = dy * params["gaze_strength_y"]
            return

        if now >= self.next_saccade_at:
            if self.state == "thinking":
                # daha dar, hafif yana kayan bakış
                self.target_gaze_x = random.uniform(2.0, params["gaze_strength_x"] * 0.55)
                self.target_gaze_y = random.uniform(-params["gaze_strength_y"] * 0.2, params["gaze_strength_y"] * 0.2)
            elif self.state == "muted":
                self.target_gaze_x = random.uniform(-2.0, 2.0)
                self.target_gaze_y = random.uniform(-1.0, 1.0)
            else:
                self.target_gaze_x = random.uniform(-params["gaze_strength_x"] * 0.4, params["gaze_strength_x"] * 0.4)
                self.target_gaze_y = random.uniform(-params["gaze_strength_y"] * 0.35, params["gaze_strength_y"] * 0.35)

            self.next_saccade_at = now + random.uniform(
                self.micro_saccade_interval_min,
                self.micro_saccade_interval_max,
            )
