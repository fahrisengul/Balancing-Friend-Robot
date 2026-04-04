import cv2
import numpy as np
import os

class PoodleFace:
    # main.py'den gelen genişlik ve yükseklik değerlerini kabul etmek için 
    # width ve height parametrelerini ekledik (varsayılan değerlerle)
    def __init__(self, width=1024, height=600, bg_filename='Poddle_v2.jpeg'):
        # Görselin yolunu belirle
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.bg_path = os.path.join(current_dir, bg_filename)
        
        # Arka plan görselini yükle
        self.base_image = cv2.imread(self.bg_path)
        
        if self.base_image is None:
            print(f"HATA: {bg_filename} bulunamadı! Yol: {self.bg_path}")
            # Görsel yoksa main.py'den gelen boyutlarda siyah ekran oluştur
            self.base_image = np.zeros((height, width, 3), dtype=np.uint8)
        else:
            # Görsel varsa, main.py'nin istediği boyuta (1024x600) yeniden boyutlandır
            self.base_image = cv2.resize(self.base_image, (width, height))
        
        self.height, self.width = self.base_image.shape[:2]
        
        # Göz merkezlerini yeni boyuta (1024x600) göre oranla
        self.eye_centers = {
            'left': (int(self.width * 0.322), int(self.height * 0.485)),
            'right': (int(self.width * 0.678), int(self.height * 0.485))
        }

    def render(self, face_data=None, camera_frame=None):
        """
        Arayüzü oluşturur.
        face_data: (x, y, w, h)
        camera_frame: Canlı kamera görüntüsü
        """
        canvas = self.base_image.copy()

        # 1. Göz Bebeklerini Hareket Ettir (Takip)
        if face_data is not None:
            fx, fy, fw, fh = face_data
            # Takip hassasiyetini ayarla
            move_x = int((fx / 640 - 0.5) * 40) 
            move_y = int((fy / 480 - 0.5) * 25)

            for side in ['left', 'right']:
                center = self.eye_centers[side]
                # Hareketli beyaz göz bebeği
                cv2.circle(canvas, (center[0] + move_x, center[1] + move_y), 
                           15, (255, 255, 255), -1) 
                # Hafif ışıma efekti
                cv2.circle(canvas, (center[0] + move_x, center[1] + move_y), 
                           18, (255, 210, 160), 2)

        # 2. Robot Vision (Küçük pencere)
        if camera_frame is not None:
            pip_w, pip_h = 240, 180
            small_frame = cv2.resize(camera_frame, (pip_w, pip_h))
            
            y_off = self.height - pip_h - 25
            x_off = self.width - pip_w - 25
            
            canvas[y_off:y_off+pip_h, x_off:x_off+pip_w] = small_frame
            cv2.rectangle(canvas, (x_off, y_off), (x_off+pip_w, y_off+pip_h), (200, 200, 200), 1)

        return canvas
