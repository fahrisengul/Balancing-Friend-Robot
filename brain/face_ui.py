import pygame
import random
import math


class PoodleFace:
    def __init__(self, width=1024, height=600):
        self.width = width
        self.height = height

        self.cx = width // 2
        self.cy = height // 2

        self.state = "idle"
        self.time = 0

        # Particle system
        self.particles = []

    # --------------------------------------------------
    # STATE
    # --------------------------------------------------
    def set_state(self, state):
        self.state = state

    def update_gaze(self, x, y):
        # artık kullanılmıyor ama API uyumluluğu için bırakıldı
        pass

    # --------------------------------------------------
    # PARTICLE SYSTEM
    # --------------------------------------------------
    def _spawn_particles(self):
        count = 2

        if self.state == "speaking":
            count = 6
        elif self.state == "thinking":
            count = 4

        for _ in range(count):
            self.particles.append({
                "x": self.cx + random.randint(-5, 5),
                "y": self.cy + random.randint(-80, 80),
                "vy": random.uniform(-2.5, -0.5),
                "life": random.randint(30, 80)
            })

    def _update_particles(self):
        new_particles = []
        for p in self.particles:
            p["y"] += p["vy"]
            p["life"] -= 1

            if p["life"] > 0:
                new_particles.append(p)

        self.particles = new_particles

    def _draw_particles(self, screen, color):
        for p in self.particles:
            alpha = max(50, min(255, p["life"] * 3))
            c = (color[0], color[1], color[2])
            pygame.draw.circle(screen, c, (int(p["x"]), int(p["y"])), 2)

    # --------------------------------------------------
    # COLOR SYSTEM
    # --------------------------------------------------
    def _get_color(self):
        return {
            "idle": (80, 100, 140),
            "listening": (80, 200, 255),
            "thinking": (180, 100, 255),
            "speaking": (255, 60, 60),
            "error": (255, 120, 0),
        }.get(self.state, (100, 100, 120))

    # --------------------------------------------------
    # DRAW
    # --------------------------------------------------
    def draw(self, screen):
        self.time += 0.05

        # Background
        screen.fill((5, 5, 10))

        color = self._get_color()

        # --------------------------------------------------
        # CORE RINGS
        # --------------------------------------------------
        pulse = math.sin(self.time * 2)

        top_y = self.cy - 120
        bottom_y = self.cy + 120

        for i in range(3):
            r = 80 + i * 10 + pulse * 3
            pygame.draw.circle(screen, color, (self.cx, int(top_y)), int(r), 2)
            pygame.draw.circle(screen, color, (self.cx, int(bottom_y)), int(r), 2)

        # --------------------------------------------------
        # ENERGY BEAM
        # --------------------------------------------------
        beam_width = 4

        if self.state == "speaking":
            beam_width = 8 + abs(math.sin(self.time * 8)) * 6
        elif self.state == "thinking":
            beam_width = 3 + abs(math.sin(self.time * 12)) * 2

        pygame.draw.line(
            screen,
            color,
            (self.cx, top_y),
            (self.cx, bottom_y),
            int(beam_width)
        )

        # --------------------------------------------------
        # PARTICLES
        # --------------------------------------------------
        self._spawn_particles()
        self._update_particles()
        self._draw_particles(screen, color)

        # --------------------------------------------------
        # CORE GLOW (fake glow)
        # --------------------------------------------------
        for i in range(3):
            radius = 40 + i * 10 + pulse * 2
            pygame.draw.circle(screen, color, (self.cx, self.cy), int(radius), 1)
