import math
import time
from typing import Optional

import numpy as np
import pygame


class PoodleCharacter:
    """
    Orb tabanlı premium AI companion UI.
    Repo uyumu için sınıf adı korunuyor.
    """

    def __init__(self, width=1024, height=600):
        self.width = width
        self.height = height

        self.state = "idle"
        self.audio_source = None

        self.start_time = time.time()
        self.last_update = time.time()

        self.center_x = width // 2
        self.center_y = height // 2

        self.orb_size = 360
        self.render_scale = 2
        self.render_size = self.orb_size * self.render_scale
        self._build_grids()

        self.smoothed_amp = 0.0
        self.smoothed_input_amp = 0.0
        self.smoothed_tts_amp = 0.0

        pygame.font.init()
        self.font = pygame.font.SysFont("Arial", 22)
        self.small_font = pygame.font.SysFont("Arial", 18)
        
    # ---------------------------------------------------------
    # PUBLIC API
    # ---------------------------------------------------------
    def bind_audio_source(self, audio_source):
        self.audio_source = audio_source

    def set_state(self, state: str):
        self.state = state or "idle"

    def update_gaze(self, x=None, y=None):
        # Orb UI için gaze kullanılmıyor; API uyumu için bırakıldı.
        return

    def update(self, dt: float = 0.016):
        input_amp = 0.0
        tts_amp = 0.0

        if self.audio_source and hasattr(self.audio_source, "get_visual_state"):
            try:
                visual = self.audio_source.get_visual_state()
                input_amp = float(visual.get("input_level", 0.0))
                tts_amp = float(visual.get("tts_level", 0.0))
            except Exception:
                pass

        self.smoothed_input_amp += (input_amp - self.smoothed_input_amp) * 0.20
        self.smoothed_tts_amp += (tts_amp - self.smoothed_tts_amp) * 0.20

        dominant = max(self.smoothed_input_amp, self.smoothed_tts_amp)
        self.smoothed_amp += (dominant - self.smoothed_amp) * 0.16

    def draw(self, screen: pygame.Surface):
        screen.fill((10, 11, 18))

        now = time.time() - self.start_time
        orb_surface = self._render_orb(now)
        orb_rect = orb_surface.get_rect(center=(self.center_x, self.center_y))
        screen.blit(orb_surface, orb_rect)

        self._draw_state_label(screen)

    # ---------------------------------------------------------
    # INTERNALS
    # ---------------------------------------------------------
    def _build_grids(self):
        s = self.render_size
        axis = np.linspace(-1.0, 1.0, s, dtype=np.float32)
        self.xx, self.yy = np.meshgrid(axis, axis)
        self.rr = np.sqrt(self.xx ** 2 + self.yy ** 2)
        self.theta = np.arctan2(self.yy, self.xx)
        
    def _state_params(self):
        base = {
            "radius": 0.78,
            "edge_glow": 1.0,
            "warp": 0.08,
            "speed": 1.0,
            "brightness": 1.0,
            "label": None,
            "palette_shift": 0.0,
        }

        if self.state == "idle":
            base.update({
                "radius": 0.79,
                "edge_glow": 0.95,
                "warp": 0.07,
                "speed": 0.8,
                "brightness": 0.95,
            })
        elif self.state == "attentive":
            base.update({
                "radius": 0.80,
                "edge_glow": 1.10,
                "warp": 0.09,
                "speed": 1.1,
                "brightness": 1.05,
                "label": "Attentive",
            })
        elif self.state == "listening":
            base.update({
                "radius": 0.82,
                "edge_glow": 1.25,
                "warp": 0.11,
                "speed": 1.3,
                "brightness": 1.10,
                "label": "Listening…",
                "palette_shift": 0.15,
            })
        elif self.state == "thinking":
            base.update({
                "radius": 0.80,
                "edge_glow": 1.15,
                "warp": 0.13,
                "speed": 0.9,
                "brightness": 1.00,
                "label": "Thinking…",
                "palette_shift": 0.30,
            })
        elif self.state == "speaking":
            base.update({
                "radius": 0.84,
                "edge_glow": 1.35,
                "warp": 0.14,
                "speed": 1.6,
                "brightness": 1.15,
                "label": "Speaking…",
                "palette_shift": 0.55,
            })
        elif self.state == "muted":
            base.update({
                "radius": 0.76,
                "edge_glow": 0.55,
                "warp": 0.03,
                "speed": 0.5,
                "brightness": 0.70,
                "label": "Muted",
            })
        elif self.state == "error":
            base.update({
                "radius": 0.82,
                "edge_glow": 1.45,
                "warp": 0.16,
                "speed": 1.8,
                "brightness": 1.10,
                "label": "Error",
                "palette_shift": 0.9,
            })

        return base

    def _render_orb(self, t: float) -> pygame.Surface:
        p = self._state_params()
    
        input_boost = self.smoothed_input_amp * 0.20 if self.state in {"listening", "attentive"} else 0.0
        tts_boost = self.smoothed_tts_amp * 0.24 if self.state == "speaking" else 0.0
        amp_boost = max(input_boost, tts_boost)
    
        radius = p["radius"] + amp_boost + 0.01 * math.sin(t * 1.2)
        warp = p["warp"] + amp_boost * 0.9
        speed = p["speed"]
        brightness = p["brightness"]
    
        # daha yumuşak deformasyon
        deform = (
            1.0
            + warp * np.sin(3.2 * self.theta + t * speed * 1.8)
            + 0.03 * np.sin(5.7 * self.theta - t * speed * 1.1)
            + 0.02 * np.sin(8.3 * self.theta + t * speed * 0.7)
        )
        deform = np.clip(deform, 0.78, 1.28)
    
        rr_warped = self.rr / deform
    
        inside = rr_warped <= radius
    
        # daha geniş ve temiz antialias edge
        edge_width = 0.045
        edge = np.clip(1.0 - np.abs(rr_warped - radius) / edge_width, 0.0, 1.0)
    
        fill = np.clip(1.0 - rr_warped / max(radius, 1e-6), 0.0, 1.0)
    
        shift = p["palette_shift"]
        f1 = np.sin((self.xx * 4.6 + self.yy * 1.5) + t * speed * 1.35 + shift)
        f2 = np.sin((self.yy * 5.0 - self.xx * 1.1) - t * speed * 1.05 + 1.7 + shift)
        f3 = np.sin((self.xx + self.yy) * 5.7 + t * speed * 0.85 + 3.0 + shift)
    
        iridescence = np.clip((edge ** 1.9) * p["edge_glow"], 0.0, 1.0)
        dark_core = np.clip(0.06 + fill * 0.16, 0.0, 1.0)
    
        r = (dark_core * 16 + iridescence * (145 + 85 * (f1 * 0.5 + 0.5))).astype(np.float32)
        g = (dark_core * 20 + iridescence * (155 + 80 * (f2 * 0.5 + 0.5))).astype(np.float32)
        b = (dark_core * 28 + iridescence * (210 + 40 * (f3 * 0.5 + 0.5))).astype(np.float32)
    
        # highlight
        highlight = np.exp(-(((self.xx + 0.28) ** 2) / 0.018 + ((self.yy + 0.34) ** 2) / 0.075))
        r += highlight * 125
        g += highlight * 125
        b += highlight * 145
    
        # state shimmer
        if self.state in {"listening", "speaking", "thinking"}:
            shimmer = (0.5 + 0.5 * np.sin((self.xx * 7.6 + self.yy * 6.8) + t * speed * 3.0)) * (edge ** 2.2)
            r += shimmer * 28
            g += shimmer * 24
            b += shimmer * 34
    
        rgb = np.stack([r, g, b], axis=-1) * brightness
        rgb = np.clip(rgb, 0, 255).astype(np.uint8)
    
        # alpha mask daha temiz
        alpha_core = inside.astype(np.float32) * 235.0
        alpha_edge = edge * 110.0
        alpha = np.clip(alpha_core + alpha_edge, 0, 255).astype(np.uint8)
    
        rgba = np.dstack([rgb, alpha]).astype(np.uint8)
        rgba = np.ascontiguousarray(rgba)
    
        hi_surface = pygame.image.frombuffer(
            rgba.tobytes(),
            (self.render_size, self.render_size),
            "RGBA",
        ).convert_alpha()
    
        # supersampling -> daha temiz kenar
        orb_surface = pygame.transform.smoothscale(
            hi_surface,
            (self.orb_size, self.orb_size)
        )
    
        return orb_surface
        
    def _draw_state_label(self, screen: pygame.Surface):
        p = self._state_params()
        label = p["label"]
        if not label:
            return

        text = self.font.render(label, True, (220, 220, 230))
        rect = text.get_rect(bottomright=(self.width - 28, self.height - 26))
        screen.blit(text, rect)
