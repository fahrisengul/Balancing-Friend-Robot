# 🧠 Poodle Robot Architecture

---

## 🎯 Amaç

Poodle, multi-modal bir child companion AI sistemidir.

Amaç:
- Tanem’i tanımak
- Onunla doğal etkileşim kurmak
- Uzun vadeli hafıza oluşturmak
- Eğitim ve duygusal destek sağlamak

---

## 🧱 Katmanlı Mimari

### 1. Perception Layer

Girdi sistemleri:

- Speech (Whisper + VAD)
- Vision (kamera + Hailo)
- OCR (doküman okuma)

---

### 2. Identity Layer

Robot “kimi görüyorum?” sorusunu cevaplar.

Bileşenler:
- Face embedding
- Voice pattern (opsiyonel)
- Relationship graph

---

### 3. Memory Layer

Türler:

- Profile memory
- Episodic memory
- Educational memory
- Relationship memory

---

### 4. Decision Layer (Brain)

Alt modüller:

- intent_router
- dialogue_manager
- response_policy
- skill_handlers
- support_policy

---

### 5. Expression Layer

- Piper TTS
- Face UI
- Behavior state machine

---

## 🔄 Veri Akışı
