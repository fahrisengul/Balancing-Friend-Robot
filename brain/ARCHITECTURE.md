| Konu / Görev | Yazılım / Kütüphane | Yazılım Karşılığı (Brain) | Donanım Karşılığı (Body) |
| :--- | :--- | :--- | :--- |
| **Ana İşlem Merkezi** | **Raspberry Pi OS (64-bit)** | Sistem Koordinatörü & OS | **Raspberry Pi 5 (8GB RAM)** |
| **Yapay Zeka (AI)** | **Hailo-8 SDK + YOLOv8** | Nesne Tanıma & Tanem'i Bulma | **Hailo-8 M.2 AI Accelerator** |
| **Görsel Arayüz** | **Pygame** | Poodle Mimik & Göz Animasyonu | **7" 1024x600 DSI IPS Ekran** |
| **Görüntü Girişi** | **OpenCV** | Kamera Yayını & Kare İşleme | **RPi Camera Module 3 Wide** |
| **Ses Çıkışı** | **Edge-TTS / gTTS** | Konuşma Sentezi (TTS) | **PAM8403 Amfi + 32mm Hoparlör** |
| **Ses Girişi** | **SpeechRecognition** | Sesli Komut Algılama (STT) | **USB veya I2S Mikrofon** |
| **Haberleşme** | **PySerial** | Hareket & Denge Komut iletimi | **GPIO / USB-UART Bridge** |
| **Güç Yönetimi** | **Python Scripts** | Batarya Takibi & Pil Uyarısı | **4S BMS + Mini560 Regülatör** |
| **Veri Depolama** | **SQLite / JSON** | Kullanıcı Hafızası & Loglar | **Samsung PM981 NVMe SSD** |
| **Soğutma** | **RPI Fan Control** | Termal Yönetim & Hız Ayarı | **Raspberry Pi Active Cooler** |


Yazılım Altyapısı (Requirements)
- Projenin taşınabilir ve stabil olması için oluşturduğumuz katmanlar:
- OpenCV & Numpy: Görüntü analizi ve matematiksel hesaplamalar için.
- PyAudio: Mikrofon erişimi için (Conda/Mac tarafındaki zorlukları aştık).
- Playsound: Ses dosyalarını bağımsız bir kanaldan çalmak için.
- Pyserial: (Gelecek adım) Robotun kafasını fiziksel olarak hareket ettirecek servolarla haberleşmek için.
