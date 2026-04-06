import pygame
import random
import os
import math
import time


class PoodleFace:
    def __init__(self, width=1024, height=600):
        self.width = width
        self.height = height

        current_dir = os.path.dirname(os.path.abspath(__file__))
        bg_path = os.path.join(current_dir, "poddle_v3.png")

        try:
            self.bg_image = pygame.image.load(bg_path).convert()
            self.bg_image = pygame.transform.scale(self.bg_image, (self.width, self.height))
            self.has_bg = True
            print(">>> [V18 - HATA DUZELTILDI & STABIL] AKTIF <<<")
        except Exception as e:
            self.has_bg = False
            print(f"Hata: {e}")

        # --- RIG AYARLARI ---
        self.FACE_RIG = {
            "eye_left_center": (425, 290),
            "eye_right_center": (605, 290),
            "eye_width": 70,
            "eye_height": 140,
            "mouth_center": (515, 355),
            "mouth_width": 56,
            "mouth_height": 26
        }

        self.COLORS = {
            "siyah": (10, 10, 10),
            "beyaz": (255, 255, 255),
            "pembe_dil": (255, 110, 130),
            "pembe_aura": (255, 182, 193, 100),
            "mavi_aura": (100, 149, 237, 100),
            "turuncu_aura": (255, 140, 0, 100),
            "gri_hud": (185, 185, 185),
            "gri_hud_soft": (150, 150, 150),
        }

        self.VALID_STATES = {
            "idle",
            "attentive",
            "listening",
            "thinking",
            "speaking",
            "muted",
            "error",
        }

        self.state = "idle"
        self.state_enter_time = time.time()

        # Eski sistem uyumluluğu
        self.eye_scale_y = 1.0
        self.target_scale_y = 1.0
        self.last_blink = pygame.time.get_ticks()
        self.next_blink_ms = random.randint(3000, 6000)

        self.pupil_size_mult = 1.0
        self.aura_color = None
        self.sleep_timer = pygame.time.get_ticks()
        self.is_sleeping = False

        self.mouth_open = 0.0
        self.talk_phase = 0.0

        # gaze hedef / current
        self.target_pos = [0.0, 0.0]
        self.current_pos = [0.0, 0.0]

        # Yeni animasyon parametreleri
        self.blink_timer = time.time() + random.uniform(2.0, 5.0)
        self.blink_duration = 0.12
        self.is_blinking = False
        self.blink_start = 0.0

        self.mouth_open_amount = 0.0
        self.breath_phase = 0.0
        self.thinking_phase = 0.0
        self.attentive_phase = 0.0

        self.gaze_x = self.width // 2
        self.gaze_y = self.height // 2
        self.target_gaze_x = self.width // 2
        self.target_gaze_y = self.height // 2

        self.next_micro_saccade = time.time() + random.uniform(0.8, 1.6)

        pygame.font.init()
        self.hud_font = pygame.font.SysFont("Arial", 18, bold=False)

    # ------------------------------------------------------------------
    # 1. set_state
    # ------------------------------------------------------------------
    def set_state(self, new_state):
        if new_state not in self.VALID_STATES:
            new_state = "idle"

        if new_state == self.state:
            return

        self.state = new_state
        self.state_enter_time = time.time()
        self.sleep_timer = pygame.time.get_ticks()
        self.is_sleeping = False

        if new_state == "speaking":
            self.target_scale_y = 0.92
            self.aura_color = self.COLORS["pembe_aura"]
            self.pupil_size_mult = 1.15
            self.mouth_open_amount = 0.25

        elif new_state == "listening":
            self.target_scale_y = 1.08
            self.aura_color = self.COLORS["mavi_aura"]
            self.pupil_size_mult = 1.08

        elif new_state == "attentive":
            self.target_scale_y = 1.03
            self.aura_color = self.COLORS["mavi_aura"]
            self.pupil_size_mult = 1.12
            self.next_micro_saccade = time.time() + random.uniform(0.6, 1.2)

        elif new_state == "thinking":
            self.target_scale_y = 0.9
            self.aura_color = self.COLORS["mavi_aura"]
            self.pupil_size_mult = 0.95
            self.next_micro_saccade = time.time() + random.uniform(0.5, 1.0)
            self.mouth_open_amount = 0.0

        elif new_state == "muted":
            self.target_scale_y = 0.5
            self.aura_color = None
            self.pupil_size_mult = 0.85
            self.mouth_open_amount = 0.0

        elif new_state == "error":
            self.target_scale_y = 0.65
            self.aura_color = self.COLORS["turuncu_aura"]
            self.pupil_size_mult = 0.8
            self.mouth_open_amount = 0.0

        else:  # idle
            self.target_scale_y = 1.0
            self.aura_color = None
            self.pupil_size_mult = 1.0
            self.mouth_open_amount = 0.0

    # ------------------------------------------------------------------
    # gaze update
    # ------------------------------------------------------------------
    def update_gaze(self, tx=None, ty=None):
        now = pygame.time.get_ticks()

        if tx is not None and ty is not None:
            self.sleep_timer = now
            self.is_sleeping = False

            self.target_gaze_x = tx
            self.target_gaze_y = ty

            gx = (tx - self.width // 2) / 120.0
            gy = (ty - self.height // 2) / 150.0
            self.target_pos = [max(-8, min(8, gx)), max(-10, min(10, gy))]
        else:
            if now - self.sleep_timer > 60000:
                self.is_sleeping = True
                self.target_scale_y = 0.02

            self.target_gaze_x = self.width // 2
            self.target_gaze_y = self.height // 2
            self.target_pos = [0.0, 0.0]

        self.current_pos[0] += (self.target_pos[0] - self.current_pos[0]) * 0.15
        self.current_pos[1] += (self.target_pos[1] - self.current_pos[1]) * 0.15

    def _smooth_gaze(self, speed=0.12):
        self.gaze_x += (self.target_gaze_x - self.gaze_x) * speed
        self.gaze_y += (self.target_gaze_y - self.gaze_y) * speed

    # ------------------------------------------------------------------
    # 2. update_animation
    # ------------------------------------------------------------------
    def update_animation(self):
        now = time.time()
        self._smooth_gaze()

        # blink
        if self.is_blinking:
            if now - self.blink_start > self.blink_duration:
                self.is_blinking = False
                self.blink_timer = now + random.uniform(2.0, 5.0)
        else:
            if now >= self.blink_timer and self.state not in ("speaking",):
                self.is_blinking = True
                self.blink_start = now

        self.breath_phase += 0.05
        self.thinking_phase += 0.08
        self.attentive_phase += 0.1

        if self.state == "idle":
            self.mouth_open_amount *= 0.85

        elif self.state == "attentive":
            if now >= self.next_micro_saccade:
                self.target_gaze_x += random.randint(-20, 20)
                self.target_gaze_y += random.randint(-12, 12)
                self.next_micro_saccade = now + random.uniform(0.8, 1.5)
            self.mouth_open_amount *= 0.8

        elif self.state == "listening":
            self.mouth_open_amount *= 0.75

        elif self.state == "thinking":
            if now >= self.next_micro_saccade:
                self.target_gaze_x += random.randint(-14, 14)
                self.target_gaze_y += random.randint(-10, 10)
                self.next_micro_saccade = now + random.uniform(0.6, 1.1)
            self.mouth_open_amount *= 0.7

        elif self.state == "speaking":
            self.mouth_open_amount = 0.35 + 0.25 * abs(math.sin(now * 9.5))

        elif self.state == "muted":
            self.mouth_open_amount = 0.0

        elif self.state == "error":
            self.mouth_open_amount *= 0.7

        self.eye_scale_y += (self.target_scale_y - self.eye_scale_y) * 0.15

    # ------------------------------------------------------------------
    # 3. _get_eye_open_ratio
    # ------------------------------------------------------------------
    def _get_eye_open_ratio(self):
        if self.is_blinking:
            return 0.08

        if self.state == "muted":
            return 0.35
        if self.state == "thinking":
            return 0.72
        if self.state == "attentive":
            return 0.88
        if self.state == "listening":
            return 0.95
        if self.state == "error":
            return 0.55
        if self.state == "speaking":
            return 0.82
        return 0.82

    # ------------------------------------------------------------------
    # 4. _get_pupil_scale
    # ------------------------------------------------------------------
    def _get_pupil_scale(self):
        if self.state == "attentive":
            return 1.08
        if self.state == "thinking":
            return 0.94
        if self.state == "muted":
            return 0.85
        if self.state == "error":
            return 0.9
        return 1.0

    # ------------------------------------------------------------------
    # 5. _compute_gaze_offset
    # ------------------------------------------------------------------
    def _compute_gaze_offset(self):
        cx = self.width / 2
        cy = self.height / 2

        dx = (self.gaze_x - cx) / cx
        dy = (self.gaze_y - cy) / cy

        max_x = 18
        max_y = 10

        if self.state == "muted":
            max_x = 8
            max_y = 5
        elif self.state == "thinking":
            max_x = 10
            max_y = 7
        elif self.state == "attentive":
            max_x = 20
            max_y = 12

        return dx * max_x, dy * max_y

    # ------------------------------------------------------------------
    # eye draw
    # ------------------------------------------------------------------
    def _draw_eye(self, screen, cx, cy, gaze_dx=0, gaze_dy=0, eye_open=1.0, pupil_scale=1.0):
        base_w = self.FACE_RIG["eye_width"]
        base_h = self.FACE_RIG["eye_height"]

        w = base_w
        h = max(4, int(base_h * eye_open * 0.9))

        x = cx + self.current_pos[0]
        y = cy + self.current_pos[1]

        if self.aura_color and not self.is_sleeping:
            aura_surf = pygame.Surface((w + 26, h + 26), pygame.SRCALPHA)
            pygame.draw.ellipse(aura_surf, self.aura_color, (0, 0, w + 26, h + 26), 3)
            screen.blit(aura_surf, (int(x - (w + 26) // 2), int(y - (h + 26) // 2)))

        eye_rect = pygame.Rect(int(x - w // 2), int(y - h // 2), int(w), int(h))
        pygame.draw.ellipse(screen, self.COLORS["siyah"], eye_rect)

        if eye_open > 0.25:
            pupil_w = int(12 * pupil_scale * self.pupil_size_mult)
            pupil_h = int(10 * pupil_scale * self.pupil_size_mult)
            pupil_x = int(x - 10 + gaze_dx * 0.35)
            pupil_y = int(y - h // 3 + gaze_dy * 0.35)
            pygame.draw.ellipse(
                screen,
                self.COLORS["beyaz"],
                (pupil_x, pupil_y, pupil_w, pupil_h)
            )

        # thinking / muted / error için üst kapak hissi
        if self.state in ("thinking", "muted", "error"):
            lid_drop = 8 if self.state == "thinking" else 14
            pygame.draw.line(
                screen,
                self.COLORS["gri_hud"],
                (eye_rect.left + 8, eye_rect.top + lid_drop),
                (eye_rect.right - 8, eye_rect.top + lid_drop),
                2
            )

    # ------------------------------------------------------------------
    # 6. _draw_mouth
    # ------------------------------------------------------------------
    def _draw_mouth(self, screen):
        mx, my = self.FACE_RIG["mouth_center"]

        if self.state == "muted":
            pygame.draw.line(
                screen,
                self.COLORS["gri_hud"],
                (int(mx - 28), int(my)),
                (int(mx + 28), int(my)),
                3
            )
            return

        if self.state == "thinking":
            rect = pygame.Rect(int(mx - 30), int(my - 5), 60, 12)
            pygame.draw.arc(screen, self.COLORS["gri_hud"], rect, 0.15, 3.0, 2)
            return

        if self.state == "speaking":
            h = int(18 + self.mouth_open_amount * 26)
            w = int(70 - self.mouth_open_amount * 8)
            pygame.draw.ellipse(
                screen,
                self.COLORS["siyah"],
                (int(mx - w // 2), int(my - h // 2), w, h)
            )
            return

        if self.is_sleeping:
            t_bob = math.sin(pygame.time.get_ticks() * 0.004) * 5
            font = pygame.font.SysFont("Arial", 24, bold=True)
            z_txt = font.render("Zzz...", True, (200, 200, 255))
            screen.blit(z_txt, (int(mx + 40), int(my - 60 + t_bob)))
            return

        if self.state in ("idle", "listening", "attentive", "error"):
            if self.state == "error":
                rect = pygame.Rect(int(mx - 28), int(my - 2), 56, 16)
                pygame.draw.arc(screen, self.COLORS["gri_hud"], rect, 3.3, 6.1, 2)
                return

            if self.state == "attentive":
                rect = pygame.Rect(int(mx - 34), int(my - 2), 68, 14)
                pygame.draw.arc(screen, self.COLORS["gri_hud"], rect, 0.05, 3.08, 2)
                return

            # idle/listening mevcut dile yakın görünüm
            t_bob = math.sin(pygame.time.get_ticks() * 0.004) * 3
            pygame.draw.ellipse(
                screen,
                self.COLORS["pembe_dil"],
                (int(mx - 15), int(my - 5), 30, int(40 + t_bob))
            )
            pygame.draw.line(
                screen,
                (200, 70, 90),
                (int(mx), int(my)),
                (int(mx), int(my + 15 + t_bob)),
                2
            )
            pygame.draw.line(
                screen,
                self.COLORS["siyah"],
                (int(mx - 20), int(my)),
                (int(mx + 20), int(my)),
                4
            )

    # ------------------------------------------------------------------
    # 7. _draw_state_hud
    # ------------------------------------------------------------------
    def _draw_state_hud(self, screen):
        text = None

        if self.state == "muted":
            text = "MUTED"
        elif self.state == "thinking":
            text = "THINKING"
        elif self.state == "attentive":
            text = "ATTENTIVE"
        elif self.state == "listening":
            text = "LISTENING"
        elif self.state == "error":
            text = "ERROR"

        if not text:
            return

        surf = self.hud_font.render(text, True, self.COLORS["gri_hud"])
        screen.blit(surf, (24, 20))

    # ------------------------------------------------------------------
    # 8. draw() içine entegrasyon
    # ------------------------------------------------------------------
    def draw(self, screen):
        self.update_animation()

        if self.has_bg:
            screen.blit(self.bg_image, (0, 0))
        else:
            screen.fill((18, 18, 18))

        now = pygame.time.get_ticks()
        if not self.is_sleeping and not self.is_blinking and now - self.last_blink > self.next_blink_ms:
            self.is_blinking = True
            self.blink_start = time.time()
            self.last_blink = now
            self.next_blink_ms = random.randint(3000, 8000)

        eye_open = self._get_eye_open_ratio()
        pupil_scale = self._get_pupil_scale()
        gaze_dx, gaze_dy = self._compute_gaze_offset()

        self._draw_eye(
            screen,
            *self.FACE_RIG["eye_left_center"],
            gaze_dx=gaze_dx,
            gaze_dy=gaze_dy,
            eye_open=eye_open,
            pupil_scale=pupil_scale
        )
        self._draw_eye(
            screen,
            *self.FACE_RIG["eye_right_center"],
            gaze_dx=gaze_dx,
            gaze_dy=gaze_dy,
            eye_open=eye_open,
            pupil_scale=pupil_scale
        )

        self._draw_mouth(screen)
        self._draw_state_hud(screen)

    def handle_calibration(self, key):
        pass
