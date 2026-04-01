# 🚀 Pre-Flight Check (Uçuş Öncesi Son Kontroller) - V4

Bu liste, **AI-Friend-Robot** projesinin montajı tamamlandıktan sonra, sisteme ilk kez güç verilmeden önce yapılması gereken kritik fiziksel ve elektriksel kontrolleri içerir.

---

## ⚡ 1. Elektriksel Güvenlik ve Güç (Kritik)
- [ ] **Voltaj Ölçümü:** Buck Converter çıkışı, Pi 5'e bağlanmadan önce multimetre ile ölçüldü mü? (**Hedef: 5.1V - 5.2V**)
- [ ] **BMS Bağlantısı:** 4 adet 18650 pilin seri (4S) bağlantısı ve BMS üzerindeki lehimler kısa devreye karşı kontrol edildi mi?
- [ ] **Ters Polarlar:** DC Jack girişinde artı (+) ve eksi (-) uçların doğru yönde olduğu teyit edildi mi?
- [ ] **Gevşek Kablo:** Kasa içinde fan pervanesine veya sıcak bileşenlere temas eden boşta kablo var mı?

---

## 🧠 2. Anakart ve AI Katmanı (Pi 5 + AI HAT)
- [ ] **Active Cooler:** Soğutucu blok işlemciye tam temas ediyor mu ve fan kablosu Pi 5 üzerindeki "FAN" portuna takılı mı?
- [ ] **AI HAT Montajı:** 13T Hailo-8 modülü HAT üzerine tam oturdu mu ve GPIO pinleri ile tam temas sağlıyor mu?
- [ ] **NVMe SSD:** Samsung SSD, Ugreen kutusuna tam yerleşti mi ve USB 3.0 (Mavi) portuna bağlı mı?

---

## 👁️ 3. Görüntü ve Kamera (DSI)
- [ ] **DSI Kablo Yönü:** 22-pin to 15-pin yassı kablo, hem Pi 5 hem de Waveshare 7" ekran tarafında doğru yönde ve kilitli mi?
- [ ] **Kamera Flex:** Camera Module 3'ün yassı kablosu bükülmeden ve "CAM" portuna doğru yerleşmiş mi?
- [ ] **Lens Temizliği:** Kamera lensi üzerindeki koruyucu jelatin çıkarıldı mı?

---

## 🔊 4. Ses ve Etkileşim (Faz 2)
- [ ] **USB Mikrofon:** Mikrofon dizisi kasanın önündeki iğne deliğine (pinhole) hizalandı mı?
- [ ] **Hoparlör Polaritesi:** Stereo hoparlörlerin kablo uçları amfi/kart üzerinde doğru yerlere takıldı mı?
- [ ] **İzolasyon:** Mikrofonun fan titreşiminden etkilenmemesi için yumuşak yataklama (sünger/conta) yapıldı mı?

---

## 🛠️ 5. Mekanik ve Termal
- [ ] **Hava Akışı:** 40mm egzoz fanı havayı dışarı üfleyecek yönde mi takıldı?
- [ ] **Ekran Sabitleme:** 7" ekranın 4 adet M2.5 vidası kasanın ön paneline güvenli şekilde sıkıldı mı?
- [ ] **Düğme Kontrolü:** Ø16mm güç butonunun mekanik basma hissi ve ışık bağlantıları kontrol edildi mi?

---

## 💾 6. Yazılım Hazırlığı
- [ ] **OS Yüklemesi:** SSD veya SD kart içinde 64-bit Raspberry Pi OS (Bookworm) yüklü mü?
- [ ] **Config.txt:** Ekranın çalışması için gereken `dtoverlay=vc4-kms-dsi-waveshare-panel,7_0_inch` satırı eklendi mi?

---
**⚠️ UYARI:** Yukarıdaki tüm kutucuklar işaretlenmeden ana şalteri açmayınız. Pi 5 düşük voltaja veya kısa devreye karşı hassastır.
