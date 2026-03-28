# 🤖 Balancing-Friend-Robot (Tanem'in Robot Arkadaşı)

Bu proje, bir denge robotu (balancing robot) mekaniği üzerine inşa edilmiş, **Hailo-10H** ve **Raspberry Pi 5** ile güçlendirilmiş, internet bağımsız (Full-Edge AI) çalışan bir sosyal robot arkadaş projesidir.

### 🎯 Proje Hedefleri
- **Denge Kontrolü:** İki tekerlek üzerinde kusursuz denge (STM32 PID Control).
- **Yüz Tanıma:** Tanem'i kapıda karşılayan ve tanıyan "Local Face ID".
- **Sosyal Etkileşim:** Sesli komutları anlama ve LLM (Yerel Dil Modeli) ile sohbet etme.
- **Güvenlik:** Tüm verilerin cihaz üzerinde işlendiği (Serverless/Stand-alone) mimari.

### 🧠 Sistem Mimarisi
1. **Alt Seviye (Refleks):** STM32F103C8T6 (Bluepill) + MPU-6050 (Denge ve Hareket).
2. **Üst Seviye (Zeka):** Raspberry Pi 5 + Hailo-10H AI Kit (Görüntü İşleme ve LLM).
3. **İletişim:** UART üzerinden hiyerarşik veri akışı.

### 📂 Klasör Yapısı
- `/firmware`: STM32 için yazılmış denge ve PID kodları (C++).
- `/brain`: Raspberry Pi 5 üzerinde koşan Python betikleri ve AI modelleri.
- `/docs`: Şemalar, bağlantı listeleri ve Ar-Ge günlükleri.
- `/mechanical`: 3D baskı veya şasi tasarım dosyaları.

---
*Bu proje bir baba-kız Ar-Ge yolculuğudur.*
