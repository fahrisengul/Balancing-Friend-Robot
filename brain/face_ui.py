import pygame
import random
import os
import math


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
        except:
            self.has_bg = False

        self.state = "idle"

        self.eye_scale = 1.0
        self.target_eye = 1.0

        self.mouth_open = 0.0
        self.talk_phase = 0.0

    # -------------------------------------------------

    def set_state(self, state):
        self.state = state

        if state == "thinking":
            self.target_eye = 1.2

        elif state == "speaking":
            self.target_eye = 0.9

        elif state == "muted":
            self.target_eye = 0.3

        else:
            self.target_eye = 1.0

    # -------------------------------------------------

    def update(self):
        self.eye_scale += (self.target_eye - self.eye_scale) * 0.1

    # -------------------------------------------------

    def draw(self, screen):

        if self.has_bg:
            screen.blit(self.bg_image, (0, 0))

        self._draw_eyes(screen)
        self._draw_mouth(screen)
        self._draw_state(screen)

    # -------------------------------------------------

    def _draw_eyes(self, screen):

        cx1, cy1 = 425, 290
        cx2, cy2 = 605, 290

        w = 70
        h = int(140 * self.eye_scale)

        pygame.draw.ellipse(screen, (10, 10, 10), (cx1 - w//2, cy1 - h//2, w, h))
        pygame.draw.ellipse(screen, (10, 10, 10), (cx2 - w//2, cy2 - h//2, w, h))

    # -------------------------------------------------

    def _draw_mouth(self, screen):

        mx, my = 515, 355

        if self.state == "speaking":
            self.talk_phase += 0.2
            self.mouth_open = abs(math.sin(self.talk_phase)) * 20
        else:
            self.mouth_open *= 0.8

        pygame.draw.ellipse(
            screen,
            (10, 10, 10),
            (mx - 30, my - 10, 60, int(20 + self.mouth_open))
        )

    # -------------------------------------------------

    def _draw_state(self, screen):

        font = pygame.font.SysFont("Arial", 18)

        txt = font.render(self.state.upper(), True, (200, 200, 200))
        screen.blit(txt, (20, 20))

    def update_gaze(self, x, y):
        """
        main.py uyumluluğu için gaze wrapper.
        Eğer sınıfta başka bir bakış metodu varsa onu kullanır.
        """
        if hasattr(self, "set_gaze_target"):
            return self.set_gaze_target(x, y)

        if hasattr(self, "look_at"):
            return self.look_at(x, y)

        if hasattr(self, "set_eye_target"):
            return self.set_eye_target(x, y)

        # fallback: koordinatları sakla
        self.gaze_x = x
        self.gaze_y = y
