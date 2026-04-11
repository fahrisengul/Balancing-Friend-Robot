# Poodle Robot: Sistem Mimarisi (V2.1 - Edge AI & Autonomous Behavior)

Bu döküman, Poodle Robot'un Raspberry Pi 5 ve Hailo-8 üzerinde %100 çevrimdışı, otonom ve uzun süreli hafızaya sahip çalışmasını sağlayan mimariyi tanımlar.

## 1. Mimari Özet Tablosu

| Konu / Görev | Yazılım / Kütüphane | Yazılım Karşılığı (Brain) | Donanım Karşılığı (Body) |
| :--- | :--- | :--- | :--- |
| **Ana İşlem Merkezi** | **Raspberry Pi OS (64-bit)** | Sistem Koordinatörü & İşletim Sistemi | **Raspberry Pi 5 (8GB RAM)** |
| **Yapay Zeka (NPU)** | **Hailo-8 SDK / TAPPAS** | Sinirsel İşlem Birimi Sürücüleri | **Hailo-8 M.2 AI Accelerator** |
| **Otonom Karar Mek.** | **py_trees (Behavior Tree)** | **Davranış Ağacı:** Sıkılma, Sevinme, Şarkı Söyleme | **Pi 5 CPU (Mantıksal Döngü)** |
| **Görüntü İşleme** | **Hailo-8 + YOLOv10 / Pose** | **Güçlü Vizyon:** Nesne Tanıma, El Sallama, Duygu Analizi | **Hailo-8 NPU Gücü** |
| **Uzun Süreli Hafıza** | **ChromaDB (Vector DB)** | **RAG:** Tanem ile Geçmişi Hatırlama (Ücretsiz/Hafif) | **Samsung PM981 NVMe SSD** |
| **Büyük Dil Modeli** | **Llama-3 / Phi-3 (Ollama)** | Zeka, Yaratıcı Yanıtlar & Kişilik Yönetimi | **RPi 5 CPU (Quantized)** |
| **Görsel Arayüz** | **Pygame** | Poodle Mimik & Göz Animasyonu (V18+) | **7" 1024x600 DSI IPS Ekran** |
| **Ses Girişi (STT)** | **OpenAI Whisper (Tiny/Base)** | **Offline** Duyma & Fısıltı Algılama | **USB / I2S Gürültü Engelleyici Mic** |
| **Ses Çıkışı (TTS)** | **Piper / Sherpa-ONNX** | **Offline** Doğal Türkçe Ses Sentezi | **PAM8403 Amfi + 32mm Hoparlör** |
| **Haberleşme** | **PySerial** | Hareket & Denge Komut İletimi | **GPIO / USB-UART Bridge** |
| **Güç & Soğutma** | **Python Scripts / Fan Ctrl** | Termal & Enerji Yönetimi | **Active Cooler + 4S BMS** |

## 2. Stratejik Katma Değer Katmanları

### A. Behavior Tree (Davranış Ağacı - Karar Mekanizması)
Poodle sadece bir komut beklemez, kendi "ihtiyaçları" ve "duyguları" vardır.
- **Otonom Davranışlar:** Eğer 5 dakika boyunca Tanem ile etkileşim olmazsa "Sıkılma" durumuna geçer (Gözlerini etrafta gezdirir, hafifçe esner).
- **Etkileşim Tetikleyicileri:** Tanem odaya girdiğinde (Hailo-8 tespitiyle) "Sevinme" ağacı çalışır (Mavi auradan pembeye geçiş, hızlı göz kırpma).
- **Öncelik Yönetimi:** Pil azaldığında konuşmayı kesip "Uykum geldi" diyerek enerji tasarruf moduna geçme kararı bu ağaçta verilir.

### B. ChromaDB (Vektör Veri Tabanı - Uzun Süreli Hafıza)
Tanem ile yapılan aylar süren eğitim maratonunun anahtarıdır.
- **Hafıza (RAG):** Tanem'in 2 hafta önce anlattığı bir hikayeyi veya en sevdiği meyveyi **ChromaDB** içinde vektörel olarak saklar. 
- **Hatırlama:** Tanem "Geçen gün ne demiştik?" dediğinde, LLM bu veri tabanına sorgu atar ve geçmişi hatırlar. Pi 5 üzerinde çalışan en hafif ve ücretsiz açık kaynaklı çözümdür.

### C. Hailo-8 Destekli Güçlü Görüntü İşleme
Sıradan bir kameradan fazlası:
- **Nesne Odaklı Etkileşim:** Tanem elinde bir "kitap" tutuyorsa, YOLOv10 bunu anında teşhis eder. Bu bilgi Davranış Ağacı'na gider ve Poodle "Kitap mı okuyacağız?" diye sorar.
- **Pose Estimation:** Tanem el salladığında Poodle bunu bir selamlaşma olarak algılar. Pi 5 CPU'sunu yormadan tüm bu yükü Hailo-8 üstlenir.

## 3. Pi 5 Taşıma Stratejisi
MacBook üzerinde geliştirdiğimiz bu modüler yapı, Pi 5 geldiğinde `requirements.txt` üzerinden kurulacak ve Hailo-8 sürücüleriyle (TAPPAS) birleşerek donanımsal ivmelenmeye kavuşacaktır.
