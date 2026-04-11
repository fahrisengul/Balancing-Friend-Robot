# 🤖 Balancing Friend Robot — main/docs Product Roadmap

Bu doküman robotun teknik evrimini ve ürünleşme yol haritasını sprint bazlı olarak tanımlar.

Amaç:
> Tanem için uzun süreli, güvenli, öğrenen ve bağ kurabilen bir robot arkadaş geliştirmek.

---

# 🧱 Sprint 1–4: Foundation Layer (Tamamlandı)

## Sprint 1 — Speech Intelligence
- STT (Whisper) stabilizasyonu
- VAD tuning
- Quality gate (garbled input filtreleme)
- Short natural utterance handling

👉 Sonuç:
- Robot doğru duyar
- Gürültüyü ayıklar

---

## Sprint 2 — Memory Foundation
- SQLite memory altyapısı
- memory_manager
- template sistemi

👉 Sonuç:
- Robot temel bilgi saklar

---

## Sprint 3 — Dialogue & Context
- dialogue_manager
- context continuity
- follow-up handling (temel)

👉 Sonuç:
- Robot konuşmayı sürdürebilir

---

## Sprint 4 — Character & Animation
- 2D orb-based character UI
- state machine
- audio-reactive animation (input + TTS)
- orchestrator

👉 Sonuç:
- Robot “canlı” hissi verir

---

# 🚀 Sprint 5 — Vision + Identity (Davranış + Persona)

Amaç:
Robotu kontrollü, doğal ve çocuk dostu bir karaktere dönüştürmek.

### İçerik
1. Response policy hardening  
2. Template system güçlendirme  
3. Follow-up / context continuity iyileştirme  
4. Tanem odaklı persona & relation model  
5. Çocuk dostu konuşma stili  
6. Eğitim koçu davranışı (temel)

👉 Sonuç:
- Robot saçmalamaz  
- Daha doğal konuşur  
- Tanem’e özel davranmaya başlar  

---

# 🚀 Sprint 6 — Education Engine

Amaç:
Robotu bir “öğrenme koçu”na dönüştürmek

### İçerik
1. Eğitim koçu modülü
2. Tanem persona modelinin derinleştirilmesi
3. Çocuk psikolojisine uygun response policy

👉 Sonuç:
- Robot ders çalıştırır  
- Motivasyon sağlar  
- Öğrenme sürecine dahil olur  

---

# 🚀 Sprint 7 — Memory Intelligence (RAG)

Amaç:
Robotu hatırlayan ve bağ kuran bir varlığa dönüştürmek

### İçerik
- Embedding layer
- Semantic search
- Memory retrieval (top-k)
- Prompt injection (RAG)
- Memory write policy
- Importance scoring
- Forgetting mechanism

👉 Robot artık:
- Hatırlar  
- Geçmişe referans verir  
- Kişiselleşir  

---

# 🚀 Sprint 8 — Safety & Trust Layer

Amaç:
Çocuk güvenliği ve sistem güvenilirliği

### İçerik
- İçerik filtreleme
- Riskli durum yönetimi
- Ebeveyn kontrol mekanizması
- Memory güvenlik katmanı

👉 Sonuç:
- Güvenli ürün  

---

# 🚀 Sprint 9 — Multi-Modal Identity Graph

Amaç:
Robotun sosyal çevreyi anlaması

### İçerik
- Kişi grafı (Tanem, arkadaşlar, aile)
- İlişki modeli
- Vision + memory entegrasyonu

👉 Sonuç:
- Robot insanları tanır  
- Sosyal bağ kurar  

---

# 🚀 Sprint 10 — Proactive Companion Engine

Amaç:
Robotun proaktif davranması

### İçerik
- Event scheduler
- Hatırlatma sistemi
- Günlük check-in
- Alışkanlık takibi

👉 Sonuç:
- Robot kendiliğinden konuşur  
- Gerçek arkadaş hissi oluşur  

---

# 🚀 Sprint 11 — Affective Intelligence Layer

Amaç:
Duygusal zeka kazandırmak

### İçerik
- Ses tonu analizi
- Duygu tespiti
- Empatik cevap üretimi

👉 Sonuç:
- Robot Tanem’in duygusunu anlar  
- Doğru tepki verir  

---

# 🚀 Sprint 12 — World Model / Life Dashboard

Amaç:
Tanem’in hayatını anlamak

### İçerik
- Okul, sınav, ders takibi
- Gelişim modeli
- Uzun vadeli hedef yönetimi

👉 Sonuç:
- Robot koç + arkadaş olur  
- Hayatın parçası haline gelir  

---

# 🧠 Genel Mimari Katmanlar

## 1. Intelligence
- STT / Dialogue / Memory / Education

## 2. Relationship
- Identity / Emotion / Proactive behavior

## 3. Trust
- Safety / Control / Long-term reliability

---

# 🎯 Final Hedef

Bu sistemin amacı:

> Sadece konuşan bir robot değil,  
> Tanem’in yıllarca yanında olacak  
> güvenli, akıllı ve duygusal bir arkadaş oluşturmak.
