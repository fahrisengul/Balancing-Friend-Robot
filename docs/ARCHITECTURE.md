# 📄 docs/ARCHITECTURE.md (FINAL)

# 🧠 Sistem Mimarisi (Canonical)

---

## 🎯 Amaç

Robotu:
- anlayan
- düşünen
- hatırlayan
- kişiselleşen

bir yapıya dönüştürmek.

---

## 🧩 Katmanlar

### 1. Perception
- Audio (STT)
- Vision (future)

---

### 2. Decision Layer

- intent_router → ne istiyor?
- dialogue_manager → bağlam
- response_policy → nasıl cevap?
- education_engine → öğretim
- skill_handlers → deterministic logic

---

### 3. Memory Layer (Sprint 7)

#### Bileşenler
- memory_writer → kayıt
- memory_retriever → çağırma
- memory_manager → DB yönetimi

#### Veri tipleri
- profile
- episodic
- preference
- emotional

---

### 4. Expression

- TTS
- UI
- state machine

---

## 🔁 Akış
