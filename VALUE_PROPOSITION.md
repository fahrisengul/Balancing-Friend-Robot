# Projenin Katma Değeri ve İnovasyon Noktaları

### 1. Dinamik Davranış Ağacı (Behavior Tree)
Poodle, statik bir komut-yanıt botu değildir. `py_trees` altyapısı sayesinde robotun bir "iç dünyası" vardır. 
- **Otonomluk:** Etkileşim olmadığında "merak" moduna geçmesi, kullanıcı odaya girdiğinde "tanıma ve karşılama" sekanslarını başlatması projeyi yaşayan bir karaktere dönüştürür.

### 2. Donanım Hızlandırmalı Vizyon (Hailo-8 Integration)
Piyasadaki çoğu hobi robotu CPU üzerinden görüntü işlerken, Poodle tüm yükü **Hailo-8 NPU**'ya yıkar. Bu sayede:
- Nesne tanıma yaparken konuşma sentezi veya LLM yanıtı gecikmez.
- Düşük güç tüketimi ile yüksek performanslı Edge AI sergilenir.

### 3. Vektörel Uzun Süreli Hafıza - Hybrid Memory Intelligence
Poodle:
- SQLite + semantic layer
- episodic memory
- context-aware recall

kullanır.

Bu yapı:
- edge-friendly
- düşük maliyetli
- uzun süreli öğrenmeye uygun
