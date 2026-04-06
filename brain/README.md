# Balancing Friend Robot — Brain Layer

Bu dizin, robotun yüksek seviye “beyin” katmanını içerir.

Buradaki amaç; ses, hafıza, LLM karar mekanizması ve yüz arayüzünü tek bir doğal etkileşim sistemi içinde birleştirmektir.

---

## Purpose

Brain katmanı şu sorumlulukları taşır:

- Kullanıcının konuşmasını almak
- Konuşmayı metne çevirmek
- Gerekirse clarification istemek
- İlgili hafızayı kontrollü biçimde çağırmak
- Local LLM ile doğal cevap üretmek
- Cevabı TTS ile seslendirmek
- UI durumunu yönetmek

---

## Current Architecture

Bugünkü çalışan mimari:

- **UI:** Pygame yüz arayüzü
- **Speech Input:** mikrofon + VAD + local STT pipeline
- **Speech Output:** Piper TTS
- **Reasoning:** local LLM (Llama-3 / Phi-3 / Ollama tabanlı kullanım senaryosu)
- **Memory:** lightweight memory manager + relevance filtering
- **Main Loop:** konuşma, state ve response orchestration

---

## Key Design Principles

### 1. Natural Conversation
Robot kısa, doğal ve insana yakın konuşmalıdır.

### 2. Clarification over Hallucination
Kullanıcıyı yanlış anladığında cevap uydurmak yerine tekrar istemelidir.

### 3. Memory Discipline
Memory sistemi faydalı olmalı, baskın olmamalıdır. Her cevabı doğum günü, voleybol veya sabit persona verilerine bağlamamalıdır.

### 4. Edge-first Mindset
Bugün Mac üzerinde geliştirilse de hedef ortam Raspberry Pi 5 + Hailo’dur.

---

## Main Files

- `main.py`  
  Ana orkestrasyon döngüsü

- `brain.py`  
  Persona, prompt yönetimi, memory discipline ve LLM cevabı

- `speech_engine.py`  
  Mikrofon, VAD, STT, TTS ve speech event yönetimi

- `memory_manager.py`  
  Hafıza yönetimi

- `face_ui.py`  
  Yüz arayüzü ve görsel durum yönetimi

- `vision.py`  
  Vision tarafı için ayrılmış alan

- `voice.py`  
  Ses odaklı yardımcı yapı veya legacy alan

- `ui/`  
  Ek UI bileşenleri

---

## What Is Working Today

- Konuşmayı alma
- Temel STT
- Local TTS
- LLM cevap üretimi
- Event driven ana loop
- Sessiz mod / yeniden aktifleşme
- Clarification gate için temel yapı

---

## What Needs Improvement

- Türkçe STT doğruluğu
- Daha güçlü microphone / acoustic tuning
- Echo suppression / self-hearing kontrolü
- Memory relevance ranking
- Persona stabilitesi
- RPi 5 üzerinde performans optimizasyonu

---

## Target Evolution

Bu dizin zaman içinde aşağıdaki daha katmanlı yapıya evrilebilir:

- `speech/`
- `llm/`
- `memory/`
- `ui/`
- `vision/`
- `orchestrator/`

Şu an ise hızlı iterasyon için daha kompakt tutulmaktadır.

---

## Recommended Dev Flow

1. Önce speech loop doğrulanır
2. Sonra STT kalite filtresi iyileştirilir
3. Ardından brain prompt ve memory discipline ayarlanır
4. Son olarak RPi 5 + Hailo hedef ortamına taşınır

---

## Summary

Brain katmanı bu projenin “kişiliğini” ve “doğallığını” belirler.

Başarılı bir robot için yalnızca doğru model yeterli değildir; doğru clarification, doğru memory kullanımı ve kontrollü persona gerekir.
