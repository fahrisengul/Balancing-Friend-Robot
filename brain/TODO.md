# 📝 Yazılım Geliştirme Yol Haritası (TODO)

Bu liste, Raspberry Pi 5 ve kasa geldikten sonra yazılım tarafında yapılacakları adım adım özetler.

## 🟦 Aşama 1: Temel Sistem Kurulumu
- [ ] SSD üzerine Raspberry Pi OS (64-bit) kurulumu ve SSH yapılandırması.
- [ ] Python sanal ortamının (venv) oluşturulması.
- [ ] Hailo-8 sürücülerinin ve donanım firmware'inin yüklenmesi.
- [ ] 1024x600 DSI ekran sürücülerinin ve dokunmatik kalibrasyonunun yapılması.

## 🟩 Aşama 2: Görüntü ve Yapay Zeka (Vision)
- [ ] Kamera (Module 3 Wide) bağlantısının test edilmesi.
- [ ] Hailo-8 üzerinden YOLOv8 modelinin ilk kez koşturulması.
- [ ] "Tanem'i Tanıma" (Face Recognition) modelinin entegre edilmesi.
- [ ] Nesne takibi ve mesafe tahmini algoritmalarının yazılması.

## 🟧 Aşama 3: Etkileşim ve Ses (Voice & UI)
- [ ] PAM8403 amfi ve hoparlörlerin ses testleri.
- [ ] Robotun ilk "Göz" animasyonunun (Mimikler) ekranda oynatılması.
- [ ] Sesli komut sisteminin (Hey Robot!) kurulması.
- [ ] Tanem ile sohbet için GPT veya basit bir soru-cevap motorunun bağlanması.

## 🟥 Aşama 4: Entegrasyon ve Hareket
- [ ] Vision verilerinin Robotun denge (Firmware) tarafına iletilmesi.
- [ ] Düşük batarya uyarısının ekrana yansıtılması (BMS verisi takibi).
- [ ] Robotun "Sıkılma", "Mutluluk" gibi duygusal durumlarının (State Machine) kodlanması.
