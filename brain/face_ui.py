import cv2
import numpy as np
import os

class PoodleFace: # Sınıf ismi main.py'deki 'from face_ui import PoodleFace' ile eşleşmeli
    def __init__(self, bg_filename='Poddle_v2.jpeg'):
        # Görselin yolunu MacBook klasör yapısına uygun olarak belirle
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.bg_path = os.path.join(current_dir, bg_filename)
        
        # Arka plan görselini yükle
        self.base_image = cv2.imread(self.bg_path)
        
        if self.base_image is None:
            print(f"HATA: {bg_filename} bulunamadı! Yol: {self.bg_path}")
            # Görsel bulunamazsa sistemin çökmemesi için siyah bir yedek ekran oluştur
            self.base_image = np.zeros((600, 1000, 3), dtype=np.uint8)
        
        self.height, self.width = self.base_image.shape[:2]
        
        # Poddle_v2 üzerindeki mavi halkaların yaklaşık merkezleri
        # Göz bebeklerini tam bu noktaların üzerinde hareket ettireceğiz
        self.eye_centers = {
            'left': (int(self.width * 0.322), int(self.height * 0.485)),
            'right': (int(self.width * 0.678), int(self.height * 0.485))
        }

    def render(self, face_data=None, camera_frame=None):
        """
        Arayüzü her karede yeniden oluşturur.
        face_data: (x, y, w, h) yüz koordinatları
        camera_frame: Ham kamera görüntüsü
        """
        # Her karede temiz görseli kopyalayarak başla
        canvas = self.base_image.copy()

        # 1. Göz Bebeklerini (Pupils) Çiz
        if face_data is not None:
            fx, fy, fw, fh = face_data
            # Yüzün merkezini hesapla ve basit bir takip ofseti oluştur (-15 ile +15 piksel arası)
            # (Kamera çözünürlüğünü 640x480 varsayıyoruz)
            move_x = int((fx / 640 - 0.5) * 30) 
            move_y = int((fy / 480 - 0.5) * 20)

            for side in ['left', 'right']:
                center = self.eye_centers[side]
                # Hareketli beyaz göz bebeği
                cv2.circle(canvas, (center[0] + move_x, center[1] + move_y), 
                           12, (255, 255, 255), -1) 
                # Hafif bir dış halka (opsiyonel estetik)
                cv2.circle(canvas, (center[0] + move_x, center[1] + move_y), 
                           14, (255, 220, 180), 1)

        # 2. Robot Vision (Sağ Alt Köşe PiP)
        if camera_frame is not None:
            pip_w, pip_h = 240, 180
            small_frame = cv2.resize(camera_frame, (pip_w, pip_h))
            
            # Sağ alt köşeden 20px içeride konumlandır
            y_off = self.height - pip_h - 20
            x_off = self.width - pip_w - 20
            
            # Küçük pencereyi ana görsele yapıştır
            canvas[y_off:y_off+pip_h, x_off:x_off+pip_w] = small_frame
            # İnce gri çerçeve ekle
            cv2.rectangle(canvas, (x_off, y_off), (x_off+pip_w, y_off+pip_h), (180, 180, 180), 1)

        return canvas
