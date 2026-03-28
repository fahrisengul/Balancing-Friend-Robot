# 🤖 AI-Friend-Robot (Tanem'in Robot Arkadaşı)

Bu proje, bir **4WD (4 Tekerlekli)** robot platformu üzerine inşa edilmiş, **Raspberry Pi 5** ve **Hailo-8 AI HAT+** ile güçlendirilmiş, internet bağımsız (Full-Edge AI) çalışan bir sosyal robot arkadaş projesidir.

### 🎯 Proje Hedefleri
- **Görüntü İşleme:** Tanem'i kapıda karşılayan ve tanıyan "Local Face ID" (Hailo-8 hızlandırmalı).
- **Sosyal Etkileşim:** Sesli komutları anlama ve yerel LLM (Büyük Dil Modeli) ile sohbet etme.
- **Otonom Hareket:** Ev içinde engellere çarpmadan Tanem'i takip edebilme veya yanında durabilme.
- **Gizlilik ve Güvenlik:** Tüm veri işlemenin (görüntü/ses) cihaz üzerinde yapıldığı "Sunucusuz" (Stand-alone) mimari.

### 🧠 Sistem Mimarisi
1. **Üst Seviye (Zeka):** Raspberry Pi 5 (8GB) + Raspberry Pi AI HAT+ (13 TOPS).
   - *Görev:* Yüz tanıma, ses-metin dönüşümü, LLM sohbet yönetimi.
2. **Alt Seviye (Kontrol):** STM32F103C8T6 (Bluepill).
   - *Görev:* Motor sürücü kontrolü ve sensör verilerinin işlenmesi.
3. **Soğutma:** Raspberry Pi Aktif Soğutucu (Yüksek performanslı AI işlemleri için).

### 🛠️ Güncel Donanım Durumu
- [x] Raspberry Pi AI HAT+ (13 TOPS) - *Satın Alındı*
- [x] Raspberry Pi Aktif Soğutucu - *Satın Alındı*
- [ ] Raspberry Pi 5 (8GB) - *Araştırılıyor*
- [ ] 4WD Robot Şasisi ve Motorlar - *Planlanıyor*

### 📂 Klasör Yapısı
- `/brain`: Raspberry Pi 5 üzerinde koşan Python betikleri ve AI modelleri.
- `/firmware`: STM32 için yazılmış motor kontrol ve sensör kodları (C++).
- `/docs`: Şemalar, BOM listesi ve teknik karar günlükleri (Decision Log).
- `/mechanical`: 4WD şasi ve montaj dosyaları.

---
*Bu proje, Kodelig 2026 tecrübesi üzerine inşa edilen bir baba-kız Ar-Ge yolculuğudur.*
