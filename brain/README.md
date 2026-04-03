# 🧠 Balancing Friend Robot - Brain Section

Bu dizin, Tanem'in robotunun tüm karar verme, yapay zeka, görüntü işleme ve kullanıcı arayüzü kodlarını barındırır. Sistem, Raspberry Pi 5 üzerinde koşan yüksek seviyeli Python mimarisi üzerine kurulmuştur.

## 🚀 Kullanılan Teknolojiler
- **Donanım:** Raspberry Pi 5 (8GB) & Hailo-8 (13 TOPS AI Accelerator)
- **OS:** Raspberry Pi OS (64-bit) Bookworm
- **Yapay Zeka:** Hailo-8 SDK, YOLOv8 (Nesne ve Yüz Tanıma)
- **Görüntüleme:** 1024x600 DSI IPS LCD
- **Ses:** Python `gTTS` (Text-to-Speech) & `SpeechRecognition` (STT)
- **Arayüz:** `Pygame` veya `CustomTkinter` (Mimikler ve Göz Animasyonları)

## 📂 Klasör Yapısı
- `/vision`: Kamera erişimi ve Hailo-8 nesne tanıma scriptleri.
- `/voice`: Sesli komut algılama ve konuşma sentezi modülleri.
- `/ui`: Göz mimikleri ve ekran arayüz tasarımları.
- `/logic`: Robotun ana karar verme algoritmaları (Tanem'i görünce verilecek tepkiler vb.).

## 🛠️ Kurulum Notları
Kurulum için gerekli kütüphaneler `requirements.txt` dosyasında listelenmiştir.
