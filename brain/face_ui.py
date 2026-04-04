import cv2
import numpy as np
import os

class PoodleFace:
    # main.py'den gelen width ve height değerlerini kabul etmek için parametreleri ekledik
    def __init__(self, width=1024, height=600, bg_filename='Poddle_v2.jpeg'):
        # Görselin yolunu belirle
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.bg_path = os.path.join(current_dir, bg_filename)
        
        # Arka plan görselini yükle
        self.base_image = cv2.imread(self.bg_path)
        
        if self.base_image is None:
            print(f"HATA: {bg_filename} bulunamadı! Yol: {self.bg_path}")
            # Görsel bulunamazsa main.py'nin istediği boyutlarda siyah bir yedek oluştur
            self.base_image = np.zeros((height, width, 3), dtype=np.uint8)
        else:
            # Görseli main.py'nin beklediği tam boyuta (1024x600) getiriyoruz
            self.base_image = cv2.resize(self.base_image, (width, height))
        
        self.height, self.width = self.base_image.shape[:2]
        
        # Poddle_v2 üzerindeki mavi halkaların 1024x600 boyutuna göre yeni merkezleri
        self.eye_centers = {
            'left': (int(self.width * 0.322), int(self.height * 0.485)),
            'right': (int(self.width * 0.678), int(self.height * 0.485))
        }

    def render(self, face_data=None, camera_frame=None):
        """
        Arayüzü her karede yeniden oluşturur.
        """
        canvas = self.base_image.copy()

        # 1. Göz Bebeklerini (Pupils) Çiz ve Takip Ettir
        if face_data is not None:
            fx, fy, fw, fh = face_data
            # Yüz koordinatlarına göre hafif bir göz bebeği hareketi (offset)
            move_x = int((fx / 640 - 0.5) * 40) 
            move_y = int((fy / 480 - 0.5) * 20)

            for side in ['left', 'right']:
                center = self.eye_centers[side]
                # Hareketli beyaz göz bebeği (pupil)
                cv2.circle(canvas, (center[0] + move_x, center[1] + move_y), 
                           15, (255, 255, 255), -1) 
                # Hafif bir dış ışıma/parlama
                cv2.circle(canvas, (center[0] + move_x, center[1] + move_y), 
                           18, (255, 210, 160), 2)

        # 2. Robot Vision (Sağ alt köşe PiP)
        if camera_frame is not None:
            pip_w, pip_h = 240, 180
            small_frame = cv2.resize(camera_frame, (pip_w, pip_h))
            
            y_off = self.height - pip_h - 25
            x_off = self.width - pip_w - 25
            
            # Kamera görüntüsünü ana görsele yapıştır
            canvas[y_off:y_off+pip_h, x_off:x_off+pip_w] = small_frame
            # İnce gri çerçeve
            cv2.rectangle(canvas, (x_off, y_off), (x_off+pip_w, y_off+pip_h), (200, 200, 200), 1)

        return canvas
