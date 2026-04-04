import cv2
import numpy as np
import os

class PoodleFace:
    def __init__(self, width=1024, height=600, bg_filename='Poddle_v2.jpeg'):
        # 1. Dosya Yolunu Belirle (Mac ve Linux uyumlu)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.bg_path = os.path.join(current_dir, bg_filename)
        
        # 2. Görseli Yükle ve Boyutlandır
        self.base_image = cv2.imread(self.bg_path)
        if self.base_image is None:
            print(f"UYARI: {bg_filename} bulunamadı! Siyah ekran oluşturuluyor.")
            self.base_image = np.zeros((height, width, 3), dtype=np.uint8)
        else:
            self.base_image = cv2.resize(self.base_image, (width, height))
        
        self.height, self.width = self.base_image.shape[:2]
        
        # 3. main.py'nin Beklediği Durum Değişkenleri
        self.state = "idle" # Varsayılan durum
        self.target_x = 0.5
        self.target_y = 0.5
        
        # 4. Göz Merkezleri (Poddle_v2 tasarımı için hassas koordinatlar)
        self.eye_centers = {
            'left': (int(self.width * 0.322), int(self.height * 0.485)),
            'right': (int(self.width * 0.678), int(self.height * 0.485))
        }

    def update_gaze(self, tx, ty):
        """main.py'nin 60. ve 65. satırlarında çağrılan takip metodu"""
        if tx is None or ty is None:
            self.target_x, self.target_y = 0.5, 0.5
        else:
            self.target_x, self.target_y = tx, ty

    def set_state(self, new_state):
        """Robotun modunu (listening, speaking, idle) günceller"""
        self.state = new_state

    def render(self, face_data=None, camera_frame=None):
        """Arayüzü her karede (frame) yeniden çizer"""
        canvas = self.base_image.copy()

        # Duruma göre göz rengi/efekti belirleme
        # main.py "listening" moduna geçtiğinde gözleri belirginleştirir
        glow_color = (255, 210, 160) # Standart soft turuncu/mavi
        if self.state == "listening":
            glow_color = (255, 255, 100) # Dinleme modunda parlak sarı/beyaz

        # Göz bebeklerinin hareket miktarını hesapla
        move_x = int((self.target_x - 0.5) * 45)
        move_y = int((self.target_y - 0.5) * 25)

        for side in ['left', 'right']:
            center = self.eye_centers[side]
            # Hareketli Beyaz Göz Bebeği
            cv2.circle(canvas, (center[0] + move_x, center[1] + move_y), 
                       16, (255, 255, 255), -1) 
            # Dış Işıma/Hale
            cv2.circle(canvas, (center[0] + move_x, center[1] + move_y), 
                       19, glow_color, 2)

        # Robot Vision (Sağ alt köşe PiP penceresi)
        if camera_frame is not None:
            pip_w, pip_h = 240, 180
            small_frame = cv2.resize(camera_frame, (pip_w, pip_h))
            y_off, x_off = self.height - pip_h - 25, self.width - pip_w - 25
            
            canvas[y_off:y_off+pip_h, x_off:x_off+pip_w] = small_frame
            # İnce estetik çerçeve
            cv2.rectangle(canvas, (x_off, y_off), (x_off+pip_w, y_off+pip_h), (200, 200, 200), 1)

        return canvas
