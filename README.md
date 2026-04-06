# Balancing Friend Robot

Balancing Friend Robot, Tanem için geliştirilen; doğal konuşabilen, görebilen, öğrenebilen ve ileride hareket kabiliyeti kazanacak bir edge-AI robot arkadaştır.

Bu proje bugün iki farklı çalışma modunda ele alınmaktadır:

1. **Mac Development Environment**
   - Pygame tabanlı yüz arayüzü
   - Offline / local speech pipeline
   - Local LLM entegrasyonu
   - Hızlı prototipleme ve davranış geliştirme

2. **Raspberry Pi 5 Target Environment**
   - Raspberry Pi 5 + Hailo AI HAT+
   - Kamera, mikrofon, hoparlör, dokunmatik ekran
   - Offline STT / TTS / LLM / memory / vision entegrasyonu
   - Nihai edge-AI robot platformu

---

## Current Working Status

Şu anda çalışan ana bileşenler:

- Pygame tabanlı yüz ve gaze arayüzü
- Mikrofon dinleme ve VAD tabanlı konuşma tespiti
- Offline / local STT hattı
- Local LLM ile cevap üretimi
- Piper ile lokal TTS
- Temel doğal konuşma döngüsü
- Sessiz moda geçme / “hey” ile yeniden aktifleşme

Kısmen çalışan veya iyileştirme gereken alanlar:

- Türkçe STT doğruluğu
- Yanlış STT girişlerinde daha iyi clarification
- LLM persona disiplini ve tekrar kontrolü
- Memory retrieval relevance filtering
- Robotun kendi sesini tekrar kullanıcı konuşması sanmasını azaltma
- Vision entegrasyonu
- Hailo hızlandırmalı production pipeline

Planlanan alanlar:

- Raspberry Pi 5 + Hailo üzerinde tam deployment
- Camera Module 3 ile vision
- Long-term memory iyileştirmeleri
- Wake handling ve behavior orchestration
- Mobilite / balancing / hareket katmanı

---

## Hardware Vision

- Raspberry Pi 5
- Raspberry Pi AI HAT+ / Hailo tabanlı vision acceleration
- 7" dokunmatik ekran
- USB / array mikrofon
- Stereo hoparlör
- Kamera modülü
- 3D baskı wedge / robot enclosure
- Batarya ve güç yönetimi

---

## Software Stack

- **UI:** Pygame
- **Speech-to-Text:** faster-whisper + VAD pipeline
- **Text-to-Speech:** Piper
- **LLM:** Llama-3 / Phi-3 (local)
- **Memory:** JSON / memory manager today, vector memory later
- **Vision:** Hailo accelerated pipeline (target)
- **Platform:** macOS dev + Raspberry Pi OS target

---

## Repository Structure

- `brain/`  
  Robotun karar verme, konuşma, hafıza ve UI orkestrasyonu

- `docs/`  
  BOM, tasarım spesifikasyonu, karar kayıtları ve pre-flight kontroller

- `firmware/`  
  Düşük seviye kontrol ve ileride hareket / donanım entegrasyonu

- `mechanical/`  
  Kasa, montaj ve fiziksel tasarım bileşenleri

- `README.md`  
  Projenin üst seviye görünümü

- `ROADMAPPING.md`  
  Yol haritası

- `VALUE_PROPOSITION.md`  
  Ürün değeri ve kullanım perspektifi

---

## Development Principle

Bu repo bir “tek seferlik demo” değil; adım adım ürünleşen bir edge-AI robot platformudur.

Bu yüzden her özellik için şu ayrım önemlidir:

- **Working today**
- **Needs tuning**
- **Planned for RPi 5 + Hailo**

---

## Documentation

Detaylı teknik belgeler:

- `docs/BOM.md`
- `docs/DESIGN_SPEC.md`
- `docs/Decision-Log.md`
- `docs/Pre-Flight-Check.md`

---

## Short Roadmap

### Phase 1 — Conversational Desktop Prototype
- Local speech loop
- UI / face rig
- LLM persona
- Memory discipline
- Clarification handling

### Phase 2 — Edge-AI Terminal
- Raspberry Pi 5 migration
- Hailo vision integration
- Camera + microphone + speaker integration
- Offline reliability improvements

### Phase 3 — Embodied Robot
- Physical mobility
- Behavior orchestration
- Advanced interaction
- Long-term learning

---

## Maintainer

Fahri Şengül

Tanem için, geleceğin teknolojisini bugünden erişilebilir kılma hedefiyle geliştirilmektedir.
