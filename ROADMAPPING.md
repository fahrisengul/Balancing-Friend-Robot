# 🗺️ AI-Friend-Robot Proje Yol Haritası (Roadmap) - V4

Bu döküman, **AI-Friend-Robot** projesinin kavramsal aşamadan, Tanem ile etkileşime geçeceği nihai ana kadar olan stratejik adımlarını içerir.

---

## 📍 Mevcut Durum: Faz 1 Satın Alma ve Tasarım Onay Aşamasında

### 🔵 Faz 1: Kontrol ve Terminal (Donanım Altyapısı)
*Hedef: Sistemin stabil çalışması, ekran ve güç yönetiminin tamamlanması.*

1.  **Donanım Tedariği (Nisan 1. Hafta):**
    * [x] RPi AI HAT+ (13T) Satın Alındı.
    * [x] RPi Active Cooler Satın Alındı.
    * [ ] RPi 5 (8GB) Stok Bekleniyor.
    * [ ] Waveshare 7" DSI LCD (C) Sipariş Edilecek.
2.  **Kasa Tasarımı (Nisan 2. Hafta):**
    * [ ] "Premium Wedge V4" tasarım taslaklarının onaylanması.
    * [ ] 3D Baskı (PETG) prototip üretimi.
3.  **Güç ve Montaj (Nisan 3. Hafta):**
    * [ ] 4S Li-ion DIY Pil Grubu ve BMS montajı.
    * [ ] Buck Converter 5.1V voltaj kalibrasyonu.
    * [ ] İlk Boot (Pre-Flight Check protokolü ile).

---

### 🎙️ Faz 2: Duyular ve Etkileşim (Yazılım ve Yapay Zeka)
*Hedef: Robotun Tanem'i tanıması, duyması ve yanıt vermesi.*

1.  **Ses ve Görüntü Entegrasyonu (Mayıs 1. Hafta):**
    * [ ] USB Mikrofon ve Stereo Hoparlörlerin kasaya montajı.
    * [ ] Camera Module 3 Autofocus testleri.
2.  **AI Yazılım Katmanı (Mayıs 2-3. Hafta):**
    * [ ] Hailo-8 (13T) sürücülerinin ve demo modellerin (Nesne Tanıma) kurulumu.
    * [ ] Python tabanlı "Zeka Motoru" (Local LLM veya OpenAI API) entegrasyonu.
3.  **Kullanıcı Deneyimi (Mayıs Sonu):**
    * [ ] Tanem için özel arayüzün (GUI) geliştirilmesi.
    * [ ] Tanem'in yüzünü tanıma ve isme göre selamlama fonksiyonu.

---

### ⚙️ Faz 3: Hareket ve Otonomi (Gelecek Vizyonu)
*Hedef: Robotun masaüstünden zemine inmesi ve bağımsız hareket etmesi.*

1.  **Tahrik Sistemi:** JGB37-520 Motorlar ve 100mm Tekerleklerin montajı.
2.  **Otonom Sürüş:** HC-SR04 Mesafe Sensörleri ile engel sakınma algoritması.
3.  **Stabilizasyon:** MPU-6050 ile denge ve yön tayini kontrolü.

---

## 📈 Başarı Kriterleri (KPIs)
* **Termal:** Yük altında (AI çalışırken) Pi 5 sıcaklığı 65°C'yi geçmemeli.
* **Güç:** Tek şarjla en az 4 saat aktif kullanım sağlanmalı.
* **Ses:** Tanem'in 2 metre mesafeden verdiği komutlar %90 doğrulukla algılanmalı.

---
*Not: Bu roadmap, parça tedarik sürelerine ve tasarım revizyonlarına bağlı olarak güncellenebilir.*
