import cv2
import numpy as np
import os

class PoodleFace:
    def __init__(self, width=1024, height=600, bg_filename='Poddle_v2.jpeg'):
        # 1. Dosya Yolunu Belirle
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.bg_path = os.path.join(current_dir, bg_filename)
        
        # 2. Görseli Yükle
        self.base_image = cv2.imread(self.bg_path)
        
        if self.base_image is None:
            print(f"UYARI: {bg_filename} bulunamadı! Siyah ekran oluşturuluyor.")
            self.base_image = np.zeros((height, width, 3), dtype=np.uint8)
        else:
            self.base_image = cv2.resize(self.base_image, (width, height))
        
        self.height, self.width = self.base_image.shape[:2]
        
        # 3. main.py'nin Beklediği Değişkenler
        self.state = "idle"  # Başlangıç durumu (idle, listening, speaking vb.)
        self.target_x = 0.5
        self.target_y = 0.5
        
        # 4. Göz Merkezleri (Poddle_v2 1024x600 için optimize)
        self.eye_centers = {
            'left': (int(self.width * 0.322), int(self.height * 0.485)),
            'right': (int(self.width * 0.678), int(self.height * 0.485))
        }

    def update_gaze(self, tx, ty):
        """Bakış koordinatlarını günceller"""
        if tx is None or ty is None:
            self.target_x = 0.5
            self.target_y = 0.5
        else:
            self.target_x = tx
            self.target_y = ty

    def set_state(self, new_state):
        """Robotun durumunu günceller (main.py çağırabilir)"""
        self.state = new_state

    def render(self, face_data=None, camera_frame=None):
        """Arayüzü her döngüde çizer"""
        canvas = self.base_image.copy()

        # Duruma göre gözlerin rengini veya davranışını değiştirebiliriz
        # Örneğin: Dinlerken (listening) gözler hafifçe parlayabilir
        pupil_color = (255, 255, 255) # Varsayılan beyaz
        if self.state == "listening":
            pupil_color = (255, 255, 150) # Hafif sarımsı/parlak

        # Göz bebekleri hareketi
        move_x = int((self.target_x - 0.5) * 40)
        move_y = int((self.target_y - 0.5) * 20)

        for side in ['left', 'right']:
            center = self.eye_centers[side]
            # Hareketli göz bebeği
            cv2.circle(canvas, (center[0] + move_x, center[1] + move_y), 
                       15, pupil_color, -1) 
            # Işıma efekti
            cv2.circle(canvas, (center[0] + move_x, center[1] + move_y), 
                       18, (255, 210, 160), 2)

        # Robot Vision (Sağ alt köşe)
        if camera_frame is not None:
            pip_w, pip_h = 240, 180
            small_frame = cv2.resize(camera_frame, (pip_w, pip_h))
            y_off, x_off = self.height - pip_h - 25, self.width - pip_w - 25
            canvas[y_off:y_off+pip_h, x_off:x_off+pip_w] = small_frame
            cv2.rectangle(canvas, (x_off, y_off), (x_off+pip_w, y_off+pip_h), (200, 200, 200), 1)

        return canvas
