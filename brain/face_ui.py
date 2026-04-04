import cv2
import numpy as np
import os

class PoodleFace:
    def __init__(self, width=1024, height=600, bg_filename='Poddle_v2.jpeg'):
        # Görselin yolunu belirle
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.bg_path = os.path.join(current_dir, bg_filename)
        
        # Arka plan görselini yükle
        self.base_image = cv2.imread(self.bg_path)
        
        if self.base_image is None:
            print(f"HATA: {bg_filename} bulunamadı! Yol: {self.bg_path}")
            # Görsel yoksa siyah ekran oluştur
            self.base_image = np.zeros((height, width, 3), dtype=np.uint8)
        else:
            # Görseli istenen boyuta ölçekle
            self.base_image = cv2.resize(self.base_image, (width, height))
        
        self.height, self.width = self.base_image.shape[:2]
        
        # Bakış koordinatları (Varsayılan: Orta nokta)
        self.target_x = 0.5
        self.target_y = 0.5
        
        # Göz merkezleri (Poddle_v2 1024x600 için optimize)
        self.eye_centers = {
            'left': (int(self.width * 0.322), int(self.height * 0.485)),
            'right': (int(self.width * 0.678), int(self.height * 0.485))
        }

    def update_gaze(self, tx, ty):
        """
        Main.py'den gelen hedef koordinatları günceller.
        tx ve ty None gelirse gözleri merkeze sabitler.
        """
        if tx is None or ty is None:
            self.target_x = 0.5
            self.target_y = 0.5
        else:
            self.target_x = tx
            self.target_y = ty

    def render(self, face_data=None, camera_frame=None):
        """Arayüzü her döngüde yeniden oluşturur"""
        canvas = self.base_image.copy()

        # Göz bebeklerini (Pupils) hareket ettir
        # 0.5 merkez olmak üzere ofset hesapla
        move_x = int((self.target_x - 0.5) * 45)
        move_y = int((self.target_y - 0.5) * 25)

        for side in ['left', 'right']:
            center = self.eye_centers[side]
            # Hareketli beyaz göz bebeği
            cv2.circle(canvas, (center[0] + move_x, center[1] + move_y), 
                       16, (255, 255, 255), -1) 
            # Hafif mavi/turuncu dış ışıma
            cv2.circle(canvas, (center[0] + move_x, center[1] + move_y), 
                       19, (255, 210, 160), 2)

        # Robot Vision (Sağ alt köşe - PiP)
        if camera_frame is not None:
            pip_w, pip_h = 240, 180
            small_frame = cv2.resize(camera_frame, (pip_w, pip_h))
            y_off = self.height - pip_h - 25
            x_off = self.width - pip_w - 25
            
            # Görüntüyü yapıştır ve çerçevele
            canvas[y_off:y_off+pip_h, x_off:x_off+pip_w] = small_frame
            cv2.rectangle(canvas, (x_off, y_off), (x_off+pip_w, y_off+pip_h), (200, 200, 200), 1)

        return canvas
