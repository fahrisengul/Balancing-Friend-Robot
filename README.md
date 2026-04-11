# 🤖 Balancing Friend Robot

Tanem için güvenli, öğrenen ve bağ kurabilen bir robot arkadaş.

---

## 🎯 Vizyon

Bu proje:
> sadece konuşan bir robot değil,  
> Tanem’in yıllarca yanında olacak  
> akıllı, güvenli ve kişiselleşen bir companion üretmeyi amaçlar.

---

## 🧠 Sistem Katmanları

### 1. Perception
- STT (Whisper)
- Vision (Hailo - planlı)

### 2. Decision
- Intent Router
- Dialogue Manager
- Response Policy
- Education Engine

### 3. Memory (Sprint 7)
- SQLite (profile + episodic)
- Memory Writer
- Memory Retriever
- (yakında) Vector Search (FAISS)

### 4. Expression
- TTS (Piper)
- UI (Pygame)
- Behavior State Machine

---

## 🚀 Çalıştırma

```bash
python main.py
