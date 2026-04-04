import cv2
import numpy as np
import os

class PoodleFace: # Sınıf ismini 'PoodleFace' olarak güncelledim
    def __init__(self, bg_filename='Poddle_v2.jpeg'):
        # Görselin yolunu belirle
        self.bg_path = os.path.join(os.path.dirname(__file__), bg_filename)
        self.base_image = cv2.imread(self.bg_path)
        
        if self.base_image is None:
            print(f"HATA: {bg_filename} bulunamadı! Lütfen dosyanın Robot_Sim klasöründe olduğundan emin olun.")
            # Dosya bulunamazsa siyah bir ekran oluşturur (480x800)
            self.base_image = np.zeros((480, 800, 3), dtype=np.uint8)
        
        self.height, self.width = self.base_image.shape[:2]
        
        # Mavi halkaların merkez koordinatları (Poddle_v2 için optimize edildi)
        self.eye_centers = {
            'left': (int(self.width * 0.322), int(self.height * 0.485)),
            'right': (int(self.width * 0.678), int(self.height * 0.485))
        }

    def render(self, face_data=None, camera_frame=None):
        """
        Arayüzü oluşturur.
        face_data: (x, y, w, h) formatında yüz koordinatları
        camera_frame: Canlı kamera görüntüsü
        """
        # Her karede temiz arka plan görselini kopyala
        canvas = self.base_image.copy()

        # 1. Göz Bebeklerini Hareket Ettir (Takip Hissi)
        if face_data is not None:
            fx, fy, fw, fh = face_data
            # Yüzün merkezini hesapla ve normalize et (-1 ile 1 arası)
            # 640x480 kamera çözünürlüğü varsayılmıştır
            move_x = int((fx / 640 - 0.5) * 30) 
            move_y = int((fy / 480 - 0.5) * 15)

            for side in ['left', 'right']:
                center = self.eye_centers[side]
                # Hareketli göz bebeği (pupil) - Beyaz nokta
                cv2.circle(canvas, (center[0] + move_x, center[1] + move_y), 
                           12, (255, 255, 255), -1) 
                # Hafif mavi dış halka/ışıma
                cv2.circle(canvas, (center[0] + move_x, center[1] + move_y), 
                           15, (255, 200, 150), 2)

        # 2. Robot Vision (Sağ alt köşe PiP)
        if camera_frame is not None:
            pip_size = (200, 150)
            small_frame = cv2.resize(camera_frame, pip_size)
            
            h_sm, w_sm = small_frame.shape[:2]
            y_offset = self.height - h_sm - 20
            x_offset = self.width - w_sm - 20
            
            # Küçük pencereyi yerleştir
            canvas[y_offset:y_offset+h_sm, x_offset:x_offset+w_sm] = small_frame
            # Çerçeve ekle
            cv2.rectangle(canvas, (x_offset, y_offset), (x_offset+w_sm, y_offset+h_sm), (200, 200, 200), 1)

        return canvas
