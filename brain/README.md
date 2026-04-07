# 🧠 Brain Module

---

## 🎯 Amaç

Brain katmanı robotun karar verme merkezidir.

---

## 🧩 Bileşenler

### intent_router
Kullanıcının ne istediğini belirler

### dialogue_manager
Konuşma bağlamını tutar

### response_policy
Cevabın kaynağını seçer:
- skill
- template
- LLM

### skill_handlers
Deterministic işlemler

### llm_client
LLM bağlantısı

### persona
Robot karakteri

---

## 🔁 Akış
