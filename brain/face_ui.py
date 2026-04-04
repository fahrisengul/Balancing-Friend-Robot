import cv2
import numpy as np
import os

class PoodleFaceUI:
    def __init__(self, bg_filename='Poddle_v2.jpeg'):
        # Görselin yolunu belirle (brain klasörü içinde olduğunu varsayıyoruz)
        self.bg_path = os.path.join(os.path.dirname(__file__), bg_filename)
        self.base_image = cv2.imread(self.bg_path)
        
        if self.base_image is None:
            print(f"HATA: {bg_filename} bulunamadı! Siyah ekran kullanılacak.")
            self.base_image = np.zeros((480, 800, 3), dtype=np.uint8)
        
        self.height, self.width = self.base_image.shape[:2]
        
        # Poddle_v2 görselindeki mavi halkaların merkez koordinatları (Yaklaşık)
        # Bu koordinatlar göz bebeklerinin bu halkaların içinde hareket etmesini sağlar
        self.eye_centers = {
            'left': (int(self.width * 0.322), int(self.height * 0.485)),
            'right': (int(self.width * 0.678), int(self.height * 0.485))
        }

    def render(self, face_data=None, camera_frame=None):
        """
        Main.py'den gelen verilerle arayüzü oluşturur.
        face_data: (x, y, w, h) veya None
        camera_frame: Kameradan gelen canlı görüntü
        """
        # Her karede temiz arka planı kopyala
        canvas = self.base_image.copy()

        # 1. Göz Bebeklerini Hareket Ettir (Takip Hissi)
        if face_data is not None:
            # Yüz koordinatlarını -1 ile 1 arasında normalize et
            fx, fy, fw, fh = face_data
            # Hareket miktarını sınırla (Göz bebeği halkanın dışına çıkmasın)
            move_x = int((fx / 640 - 0.5) * 30) 
            move_y = int((fy / 480 - 0.5) * 15)

            for side in ['left', 'right']:
                center = self.eye_centers[side]
                # Hareketli göz bebeği (pupil)
                cv2.circle(canvas, (center[0] + move_x, center[1] + move_y), 
                           12, (255, 255, 255), -1) # Parlak beyaz merkez
                # Hafif bir dış ışıma (glow)
                cv2.circle(canvas, (center[0] + move_x, center[1] + move_y), 
                           15, (255, 200, 150), 2)

        # 2. Robot Vision (PiP - Resim İçinde Resim)
        if camera_frame is not None:
            # Kameradan gelen görüntüyü küçük bir kare olarak sağ alta yerleştir
            pip_size = (200, 150)
            small_frame = cv2.resize(camera_frame, pip_size)
            
            h_sm, w_sm = small_frame.shape[:2]
            y_offset = self.height - h_sm - 20
            x_offset = self.width - w_sm - 20
            
            # Görüntüyü zemine yapıştır
            canvas[y_offset:y_offset+h_sm, x_offset:x_offset+w_sm] = small_frame
            # Etrafına ince bir çerçeve
            cv2.rectangle(canvas, (x_offset, y_offset), (x_offset+w_sm, y_offset+h_sm), (200, 200, 200), 1)

        return canvas

# main.py içinden kullanım örneği:
# ui = PoodleFaceUI()
# frame = ui.render(face_data=current_face, camera_frame=raw_cap)
# cv2.imshow("Poodle Brain", frame)
