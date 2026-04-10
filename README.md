# 🤖 Balancing Friend Robot

Tanem için uzun süreli, güvenli, öğrenen ve bağ kurabilen bir robot arkadaş.

---

# 🎯 Vizyon

Bu proje:
> sadece konuşan bir robot değil,  
> Tanem’in yıllarca yanında olacak  
> akıllı, güvenli ve duygusal bir companion üretmeyi amaçlar.

---

# 🧠 Sistem Genel Yapısı

## Katmanlar

### 1. Perception (Algılama)
- Mikrofon (STT)
- Kamera (Vision / Identity)
- OCR (doküman / sınav okuma)

### 2. Decision (Karar)
- Intent Router
- Dialogue Manager
- Response Policy
- Skill System

### 3. Memory (Hafıza)
- SQLite tabanlı memory
- Template system
- (Sprint 7) RAG / semantic memory

### 4. Expression (İfade)
- TTS (Piper)
- Character UI (Orb / Animation)
- State machine

---

# 🧱 Donanım

### 🎯 Hedef Platform
- Raspberry Pi 5 — **16 GB RAM**
- 7” ekran
- USB mikrofon + hoparlör
- Raspberry Pi Camera
- (opsiyonel) Hailo AI Accelerator (13 TOPS)

---

# ⚙️ Neden 16 GB?

16 GB ile sistem:

- aynı anda STT + UI + Vision + Brain çalıştırabilir
- memory + embedding + retrieval katmanını kaldırabilir
- daha büyük context ve model kullanabilir
- service-based mimariye geçebilir

👉 Hedef artık:
> single-process demo değil,  
> multi-service companion system

---

# 🚀 Çalıştırma

```bash
python main.py
