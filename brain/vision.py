import cv2
from ultralytics import YOLO

class RobotVision:
    def __init__(self):
        # Bilgisayarda simülasyon için en hafif YOLOv8 modelini (Nano) kullanıyoruz
        # Bu satır ilk çalıştığında internetten 6MB'lık küçük bir model dosyası indirebilir.
        print("Yapay Zeka Modeli Yükleniyor...")
        self.model = YOLO('yolov8n.pt') 
        
        # MacBook kamerasını aç (Genelde 0 veya 1 olur)
        self.cap = cv2.VideoCapture(0)
        
        if not self.cap.isOpened():
            print("Hata: Kamera açılamadı!")

    def get_target_coordinates(self):
        """Kameradan görüntü alır, insanı bulur ve merkez koordinatını döner."""
        ret, frame = self.cap.read()
        if not ret:
            return None, None

        # Sadece "person" (insan) sınıfını ara (class 0)
        # conf=0.5: %50 emin olmadığı kişileri göstermez
        results = self.model(frame, classes=[0], conf=0.5, verbose=False)
        
        target_center = (None, None)
        
        for r in results:
            boxes = r.boxes
            for box in boxes:
                # Koordinatları al (x1, y1 sol üst; x2, y2 sağ alt)
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                center_x = int((x1 + x2) / 2)
                center_y = int((y1 + y2) / 2)
                
                # Görsel geri bildirim (Simülasyon penceresinde kutu çiz)
                cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
                cv2.circle(frame, (center_x, center_y), 5, (0, 0, 255), -1)
                
                # Sadece ilk bulduğu kişinin merkezini hedef alalım
                target_center = (center_x, center_y)

        # Kamerayı bir pencerede göster (Test amaçlı)
        cv2.imshow("Robot Vision - Simülasyon", frame)
        
        # 'q' tuşuna basılırsa çıkış yap (Sadece test modundayken işe yarar)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            return "EXIT", "EXIT"
        
        return target_center

    def close(self):
        self.cap.release()
        cv2.destroyAllWindows()

# --- TEST BLOĞU ---
# Bu dosya doğrudan çalıştırıldığında (python vision.py) aşağıdaki kısım devreye girer.
if __name__ == "__main__":
    vision = RobotVision()
    print("Simülasyon başladı. Çıkmak için pencere üzerindeyken 'q' tuşuna basın.")
    
    try:
        while True:
            coord = vision.get_target_coordinates()
            if coord == ("EXIT", "EXIT"):
                break
            if coord[0] is not None:
                print(f"Hedef Koordinatları -> X: {coord[0]}, Y: {coord[1]}")
    except KeyboardInterrupt:
        pass
    finally:
        vision.close()
        print("Kamera kapatıldı.")
