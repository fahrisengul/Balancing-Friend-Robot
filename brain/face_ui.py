import pygame
import math
import random

class PoodleFace:
    def __init__(self, width=1024, height=600):
        self.width = width
        self.height = height

        self.state = "idle"

        self.center_x = width // 2
        self.center_y = height // 2

        self.eye_offset_x = 120
        self.eye_offset_y = -40

        self.eye_radius = 22
        self.pupil_radius = 8

        self.target_gaze = (0, 0)
        self.current_gaze = (0, 0)

        self.time = 0

        self.colors = {
            "idle": (120, 120, 140),
            "listening": (80, 160, 255),
            "thinking": (180, 100, 255),
            "speaking": (80, 255, 200),
            "error": (255, 80, 80),
        }

    def set_state(self, state):
        self.state = state

    def update_gaze(self, x, y):
        dx = (x - self.center_x) / self.width
        dy = (y - self.center_y) / self.height

        self.target_gaze = (dx * 10, dy * 10)

    def _smooth_gaze(self):
        cx, cy = self.current_gaze
        tx, ty = self.target_gaze

        self.current_gaze = (
            cx + (tx - cx) * 0.1,
            cy + (ty - cy) * 0.1
        )

    def draw(self, screen):
        self.time += 0.05
        self._smooth_gaze()

        screen.fill((15, 15, 20))  # dark background

        color = self.colors.get(self.state, (120, 120, 140))

        # --- CENTER CORE ---
        core_radius = 40 + math.sin(self.time * 2) * 3
        pygame.draw.circle(screen, color, (self.center_x, self.center_y + 60), int(core_radius), 2)

        # --- EYES ---
        left_eye = (
            self.center_x - self.eye_offset_x,
            self.center_y + self.eye_offset_y
        )

        right_eye = (
            self.center_x + self.eye_offset_x,
            self.center_y + self.eye_offset_y
        )

        for ex, ey in [left_eye, right_eye]:
            pygame.draw.circle(screen, color, (ex, ey), self.eye_radius, 2)

            gx, gy = self.current_gaze
            pupil_pos = (int(ex + gx), int(ey + gy))

            pygame.draw.circle(screen, color, pupil_pos, self.pupil_radius)

        # --- AURA / STATE EFFECT ---
        if self.state == "thinking":
            r = 80 + math.sin(self.time * 3) * 5
            pygame.draw.circle(screen, color, (self.center_x, self.center_y), int(r), 1)

        if self.state == "listening":
            r = 90 + math.sin(self.time * 4) * 8
            pygame.draw.circle(screen, color, (self.center_x, self.center_y), int(r), 1)

        if self.state == "speaking":
            wave = math.sin(self.time * 8) * 10
            pygame.draw.circle(screen, color, (self.center_x, self.center_y + 60), int(45 + wave), 2)

        if self.state == "error":
            pygame.draw.circle(screen, (255, 0, 0), (self.center_x, self.center_y), 100, 1)
