# 🤖 AI-Friend-Robot (Premium Wedge V4)

**AI-Friend-Robot**, Raspberry Pi 5 ve Hailo-8 (13T) AI hızlandırıcı tabanlı, 7 inç dokunmatik arayüze sahip, eğitim ve etkileşim odaklı bir **Edge-AI Terminalidir.** Bu proje; Tanem için bir eğitim koçu, İngilizce pratik arkadaşı ve yüksek performanslı bir yapay zeka platformu olarak tasarlanmıştır.

Poodle, sadece dengede duran bir robot değil; **Raspberry Pi 5** ve **Hailo-8** altyapısıyla güçlendirilmiş, görebilen, duyabilen ve öğrenebilen otonom bir "Eğitim Arkadaşı"dır.

---

## 🌟 Öne Çıkan Donanım Özellikleri
* **Yüksek Performanslı AI:** Raspberry Pi AI HAT+ (13T TOPS) ile gerçek zamanlı nesne tanıma ve ses işleme.
* **Premium Arayüz:** 7" Waveshare DSI IPS Dokunmatik Ekran (1024x600).
* **Kesintisiz Güç (DIY UPS):** 4S Li-ion (14.8V) batarya grubu ve 5V 5A regülatör ile mobil kullanım.
* **Gelişmiş Etkileşim:** Camera Module 3 (Autofocus), Stereo Hoparlör ve USB Mikrofon Dizisi.
* **Şık Tasarım:** 3D baskı (PETG) "Premium Wedge" masaüstü formu.


## 🚀 Öne Çıkan Yazılım ve AI Özellikler
- **Edge AI Vision:** Hailo-8 ile saniyede 100+ FPS nesne tanıma ve takip.
- **Cognitive Personality:** LLM (Llama-3) entegrasyonu ile zeki ve yaratıcı diyaloglar.
- **Autonomous Behavior:** "Behavior Tree" (Davranış Ağacı) ile sıkılma, sevinme gibi insani tepkiler.
- **Long-term Memory:** ChromaDB vektör veri tabanı ile geçmiş sohbetleri ve kullanıcı tercihlerini hatırlama.
- **100% Offline:** Gizlilik odaklı, internet gerektirmeyen STT (Whisper) ve TTS (Piper) motorları.

## 🛠 Teknoloji Yığını
- **Brain:** Raspberry Pi 5 (8GB)
- **Vision NPU:** Hailo-8 Century
- **Intelligence:** Llama-3 / Phi-3 (via Ollama)
- **UI/UX:** Pygame (V18+ Dynamic Face Rig)
- **Storage:** Samsung PM981 NVMe SSD

## 📂 Dosya Yapısı
- `face_ui.py`: Görsel motor ve mimik yönetimi.
- `speech_engine.py`: Sesli iletişim katmanı.
- `main.py`: Ana orkestrasyon ve döngü.
- `ARCHITECTURE.md`: Detaylı sistem mimarisi.

---

## 📅 Proje Fazları ve Durum

### ✅ Faz 1: Kontrol ve Terminal (Tamamlanmak Üzere)
* [x] Pi 5 & AI HAT Tedariği.
* [x] 7" DSI Ekran Seçimi ve Tasarım Entegrasyonu.
* [x] DIY Güç Sistemi (UPS) Tasarımı.
* [ ] Kasa Üretimi (3D Baskı - Süreçte).

### 🎙️ Faz 2: Duyular ve Etkileşim (Planlama Aşamasında)
* [ ] Sesli Komut ve Yanıt Sistemi (Python + OpenAI/Local LLM).
* [ ] Tanem için Yüz Tanıma ve Özelleştirilmiş Eğitim Modülleri.
* [ ] USB Mikrofon ve Stereo Hoparlör Montajı.

### ⚙️ Faz 3: Hareket ve Mobilite (Gelecek Vizyonu)
* [ ] 4WD Tahrik Sistemi ve Otonom Sürüş.

---

## 🛠️ Hızlı Başlangıç ve Dökümantasyon
Projenin detaylı teknik dökümanlarına aşağıdaki linklerden ulaşabilirsiniz:

1. [📋 **BOM.md**](./BOM.md): Malzeme Listesi ve Bütçe Takibi.
2. [⚙️ **DESIGN_SPEC.md**](./DESIGN_SPEC.md): Kasa Tasarımı ve Teknik Çizim Ölçüleri.
3. [🚀 **Pre-Flight-Check.md**](./Pre-Flight-Check.md): İlk Çalıştırma Öncesi Kontrol Listesi.

---

## 🔋 Güç ve Termal Strateji
Sistem, 4 adet 18650 pilden oluşan 4S paketi üzerinden beslenir. Isı yönetimi, Pi 5 Active Cooler ve kasa arkasındaki 40mm tahliye fanı ile sağlanan bir hava tüneli üzerinden gerçekleştirilir.

---

## 👨‍💻 Geliştirici
**Fahri** | *Teknoloji Hub & Ekosistem Stratejisti*

*"Tanem için, geleceğin teknolojisiyle bugün tanışma fırsatı."*
