# 🐶 Poodle Robot — Child Companion AI

Poodle, Raspberry Pi üzerinde çalışan, çocuk odaklı, uzun süreli ilişki kurabilen bir yapay zeka robotudur.

Bu proje bir “konuşan oyuncak” değil;
bir **arkadaş, refakatçi, eğitim koçu ve güvenli dijital hafıza sistemi** olarak tasarlanmıştır.

---

## 🎯 Vizyon

Poodle:
- Tanem’i tanır
- Onunla bağ kurar
- Arkadaşlarını öğrenir
- Eğitim sürecini destekler
- Duygusal olarak yanında olur
- Yıllar içinde gelişen bir hafıza oluşturur

---

## 🧠 Sistem Yaklaşımı

LLM merkezli değil,
**Orchestration + Memory + Perception merkezli mimari**

---

## 🧱 Ana Katmanlar

1. **Perception**
   - Mikrofon (STT + VAD)
   - Kamera (vision)
   - OCR / belge okuma

2. **Identity & Memory**
   - Kişi tanıma
   - İlişki grafı
   - Uzun vadeli hafıza

3. **Decision (Brain)**
   - Intent router
   - Dialogue manager
   - Skill system
   - Safety policy

4. **Expression**
   - TTS (Piper)
   - Yüz animasyonu
   - Davranış (state machine)

---

## ⚙️ Donanım Hedefi

- Raspberry Pi 5 (16 GB)
- Hailo AI Accelerator (13 TOPS)
- Pi Camera
- USB Mikrofon + Hoparlör
- 7” ekran

---

## 🧭 Yol Haritası

### Faz 1 — Core AI
- [x] Speech pipeline (Whisper + VAD + Piper)
- [x] Brain v1 (LLM + intent)
- [x] Face UI

### Faz 2 — Brain Refactor (aktif)
- [ ] Dialogue manager
- [ ] Response policy
- [ ] Deterministic skills
- [ ] Memory relevance

### Faz 3 — Identity & Vision
- [ ] Kişi tanıma
- [ ] Takip sistemi
- [ ] Arkadaş öğrenme

### Faz 4 — Education Engine
- [ ] Sınav tarama
- [ ] LGS hazırlık sistemi
- [ ] Öğrenme profili

### Faz 5 — Emotional Support
- [ ] Support policy
- [ ] Risk detection
- [ ] Parent awareness

---

## 🚨 Tasarım İlkeleri

- Çocuk güvenliği önceliklidir
- Uydurma bilgi üretme
- Kısa ve doğal konuş
- Gereksiz tekrar yapma
- Hafızayı kontrollü kullan

---

## 📌 Mevcut Durum

- STT pipeline stabil
- TTS stabil
- Basic conversational loop çalışıyor
- Quality gate aktif
- Brain refactor süreci başladı

## 📎 Not

Bu proje uzun vadeli bir AI companion sistemidir.
Mimari sadelikten çok **doğru katman ayrımı** hedeflenmiştir.
