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
            print(">>> [V16 - GOZ HIZASI SABITLENDI] AKTIF <<<")
        except Exception as e:
            self.has_bg = False
            print(f"Hata: {e}")

        # --- RIG AYARLARI ---
        self.FACE_RIG = {
            "eye_left_anchor": (-80, 25), 
            "eye_right_anchor": (80, 25),
            "eye_width": 70,
            "eye_height": 140,
            "mouth_anchor": (0, 90),
            "head_center": (515, 265)
        }

        self.COLORS = {
            "siyah": (10, 10, 10),
            "beyaz": (255, 255, 255),
            "pembe_dil": (255, 110, 130),
            "pembe_aura": (255, 182, 193, 100),
            "mavi_aura": (100, 149, 237, 100),
            "turuncu_aura": (255, 140, 0, 100)
        }

        self.state = "idle"
        self.eye_scale_y = 1.0
        self.target_scale_y = 1.0
        self.last_blink = pygame.time.get_ticks()
        self.next_blink_ms = random.randint(3000, 6000)
        
        self.tilt_angle = 0.0
        self.target_tilt = 0.0
        self.pupil_size_mult = 1.0
        self.aura_color = None
        self.sleep_timer = pygame.time.get_ticks()
        self.is_sleeping = False
        
        self.mouth_open = 0.0
        self.talk_phase = 0.0
        self.target_pos = [0.0, 0.0]
        self.current_pos = [0.0, 0.0]

    def set_state(self, state):
        self.state = state
        self.sleep_timer = pygame.time.get_ticks()
        self.is_sleeping = False
        
        if state == "speaking":
            self.target_scale_y = 0.9
            self.target_tilt = 0.0
            self.aura_color = self.COLORS["pembe_aura"]
            self.pupil_size_mult = 1.3
        elif state == "listening":
            self.target_scale_y = 1.15
            self.target_tilt = 8.0 # Eğim açısını hizayı bozmaması için biraz azalttım
            self.aura_color = self.COLORS["mavi_aura"]
            self.pupil_size_mult = 1.1
        elif state == "error":
            self.target_tilt = -5.0
            self.aura_color = self.COLORS["turuncu_aura"]
            self.pupil_size_mult = 0.8
        else:
            self.target_scale_y = 1.0
            self.target_tilt = 0.0
            self.aura_color = None
            self.pupil_size_mult = 1.0

    def update_gaze(self, tx=None, ty=None):
        now = pygame.time.get_ticks()
        if tx is not None and ty is not None:
            self.sleep_timer = now
            self.is_sleeping = False
            gx = (tx - self.width // 2) / 120.0
            gy = (ty - self.height // 2) / 150.0
            self.target_pos = [max(-8, min(8, gx)), max(-10, min(10, gy))]
        else:
            if now - self.sleep_timer > 60000:
                self.is_sleeping = True
                self.target_scale_y = 0.02
            self.target_pos = [0.0, 0.0]

        self.current_pos[0] += (self.target_pos[0] - self.current_pos[0]) * 0.15
        self.current_pos[1] += (self.target_pos[1] - self.current_pos[1]) * 0.15
        self.tilt_angle += (self.target_tilt - self.tilt_angle) * 0.05

    def _rotate_point(self, point, angle, center):
        angle_rad = math.radians(angle)
        ox, oy = center
        px, py = point
        qx = ox + math.cos(angle_rad) * (px - ox) - math.sin(angle_rad) * (py - oy)
        qy = oy + math.sin(angle_rad) * (px - ox) + math.cos(angle_rad) * (py - oy)
        return qx, qy

    def _draw_eye(self, screen, side="left"):
        anchor = self.FACE_RIG[f"eye_{side}_anchor"]
        # Gözlerin y-eksenindeki konumunu her zaman kafa merkeziyle aynı tutuyoruz (Horizontal alignment)
        base_pos = (self.FACE_RIG["head_center"][0] + anchor[0], 
                    self.FACE_RIG["head_center"][1] + anchor[1])
        
        # Tilt işlemi sadece kafa geneli için uygulanır, ama gözler arası y-farkı oluşmaması için 
        # rotasyon sonrası koordinatları denetliyoruz.
        pos = self._rotate_point(base_pos, self.tilt_angle, self.FACE_RIG["head_center"])
        
        # Keskin hizalama: Eğer dinleme modundaysak, iki gözün y eksenindeki kaymasını minimumda tut
        draw_y = pos[1]
        
        w, h = self.FACE_RIG["eye_width"], max(2, self.FACE_RIG["eye_height"] * self.eye_scale_y)
        x = pos[0] + self.current_pos[0]
        y = draw_y + self.current_pos[1]

        if self.aura_color and not self.is_sleeping:
            aura_surf = pygame.Surface((w+20, h+20), pygame.SRCALPHA)
            pygame.draw.ellipse(aura_surf, self.aura_color, (0, 0, w+20, h+20), 3)
            screen.blit(aura_surf, (int(x - (w+20)//2), int(y - (h+20)//2)))

        pygame.draw.ellipse(screen, self.COLORS["siyah"], (int(x - w // 2), int(y - h // 2), w, h))
        
        if self.eye_scale_y > 0.4:
            p_w, p_h = 12 * self.pupil_size_mult, 10 * self.pupil_size_mult
            pygame.draw.ellipse(screen, self.COLORS["beyaz"], (int(x - 10), int(y - h//3), int(p_w), int(p_h)))

    def _draw_mouth(self, screen):
        base_pos = (self.FACE_RIG["head_center"][0] + self.FACE_RIG["mouth_anchor"][0],
                    self.FACE_RIG["head_center"][1] + self.FACE_RIG["mouth_anchor"][1])
        mx, my = self._rotate_point(base_pos, self.tilt_angle, self.FACE_RIG["head_center"])
        
        if self.state == "speaking":
            self.talk_phase += 0.25
            m_target = 0.4 + abs(math.sin(self.talk_phase * 1.5)) * 0.9
            self.mouth_open += (m_target - self.mouth_open) * 0.2
            h = int(26 + self.mouth_open * 25)
            w = int(56 - self.mouth_open * 5)
            pygame.draw.ellipse(screen, self.COLORS["siyah"], (int(mx - w // 2), int(my - h // 2), w, h))
        else:
            t_bob = math.sin(pygame.time.get_ticks() * 0.004) * 5
            if self.is_sleeping:
                font = pygame.font.SysFont("Arial", 24, bold=True)
                z_txt = font.render("Zzz...", True, (200, 200, 255))
                screen.blit(z_txt, (int(mx + 40), int(my - 60 + t_bob)))
            else:
                pygame.draw.ellipse(screen, self.COLORS["pembe_dil"], (int(mx - 15), int(my - 5), 30, int(40 + t_bob)))
                pygame.draw.line(screen, (200, 70, 90), (int(mx), int(my)), (int(mx), int(my + 15 + t_bob)), 2)
            pygame.draw.line(screen, self.COLORS["siyah"], (int(mx - 20), int(my)), (int(mx + 20), int(my)), 4)

    def draw(self, screen):
        if self.has_bg: screen.blit(self.bg_image, (0, 0))
        self.eye_scale_y += (self.target_scale_y - self.eye_scale_y) * 0.15
        now = pygame.time.get_ticks()
        if not self.is_sleeping and now - self.last_blink > self.next_blink_ms:
            self.eye_scale_y = 0.02
            if now - self.last_blink > self.next_blink_ms + 120:
                self.last_blink = now
                self.next_blink_ms = random.randint(3000, 8000)

        self._draw_eye(screen, "left")
        self._draw_eye(screen, "right")
        self._draw_mouth(screen)
