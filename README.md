# 🤖 AI-Friend-Robot (Project: Tanem's Companion)

Bu proje, Raspberry Pi 5 ve Edge-AI teknolojilerini kullanarak geliştirilen, orta boy bir Poodle boyutlarında, 4 tekerlekli (4WD) otonom bir robot projesidir. Projenin ana amacı, **Tanem** için etkileşimli, yüz tanıyan ve sesli komutlarla iletişim kurabilen akıllı bir robot arkadaş geliştirmektir.

---

## 🚀 Proje Vizyonu
* **Boyut:** Orta Boy Poodle (Heybetli ve stabil gövde).
* **Zeka:** Raspberry Pi 5 (8GB) + Raspberry Pi AI HAT+ (13 TOPS) ile yerel yapay zeka.
* **Hareket:** 4 adet JGB37-520 (333 RPM) yüksek torklu enkoderli motor.
* **Dayanıklılık:** Her motor için bağımsız TB6612FNG sürücü (Redundancy & Termal Kararlılık).
* **Hafıza:** Samsung PM981 NVMe SSD + Ugreen USB 3.1 Gen2 yüksek hızlı depolama.

---

## 🏗️ Sistem Mimarisi

### 1. Beyin (Yüksek Seviye)
* **Raspberry Pi 5 (8GB):** Görüntü işleme, doğal dil işleme ve genel mantık katmanı.
* **SSD Depolama:** İşletim sistemi ve LLM modellerinin hızlı yüklenmesi için NVMe çözümü.
* **Soğutma:** Pi 5 ve AI modülü için aktif fanlı soğutucu blok.

### 2. Omurilik (Alt Seviye)
* **STM32F103C8T6 (Bluepill):** 72MHz hızında motor kontrolü, sensör füzyonu ve gerçek zamanlı tepkiler.
* **Geri Bildirim:** Manyetik enkoderler ile milimetrik yol ölçümü (Odometry).

### 3. Enerji Sistemi
* **Batarya:** 4S 18650 Li-ion Paket (14.8V Nominal).
* **Koruma:** Olt 4S 40A Balanslı BMS (Mor Seri).
* **Şarj:** 16.8V 2A CC/CV Akıllı Şarj Sistemi.

---

## 📂 Proje Yapısı
* `/docs`: Donanım seçimleri (BOM), güç sistemi ve mimari detaylar.
* `/firmware`: STM32 için C++ / Bare-metal kodları.
* `/ai_models`: Yüz tanıma ve ses işleme modelleri.
* `/scripts`: Raspberry Pi 5 yönetim ve entegrasyon scriptleri.

---

## 📝 Güncel Durum (Mart 2026)
- [x] AI Hızlandırıcı ve Soğutucu temin edildi.
- [x] SSD ve USB 3.1 NVMe Kutusu kararlaştırıldı.
- [x] Motor (JGB37) ve Sürücü (4x TB6612) konfigürasyonu onaylandı.
- [x] Güç sistemi (4S BMS + Adaptör) kesinleşti.
- [ ] STM32 Bluepill ve ST-Link V2 (Sipariş bekleniyor).
- [ ] Raspberry Pi 5 (Stok bekleniyor).

---

## 🤝 Katkıda Bulunanlar
* **Fahri:** Proje Lideri & Donanım Mimarı.
* **Tanem:** Robotun En Yakın Arkadaşı & Test Pilotu.
* **Gemini:** Mühendislik Danışmanı.

---
*Bu proje "Donanım Kararlılığı ve Güvenlik" önceliğiyle geliştirilmektedir.*
