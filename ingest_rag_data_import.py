import json
import numpy as np
from sentence_transformers import SentenceTransformer
from memory.vector_index import VectorIndex

# 1. Ayarlar
DATA_PATH = "chunks_v2.json"
MODEL_NAME = "all-MiniLM-L6-v2" # Senin VECTOR_DIM=384 ayarına tam uyan model

def start_ingest():
    print(">>> [INGEST] Başlatılıyor...")
    
    # 2. Modeli Yükle (Edge uyumlu, hafif)
    model = SentenceTransformer(MODEL_NAME)
    v_index = VectorIndex() # Senin vector_index.py dosyanı kullanır

    # 3. Veriyi Oku
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        chunks = json.load(f)

    print(f">>> {len(chunks)} adet chunk okunuyor...")

    for i, item in enumerate(chunks):
        # Arama için zenginleştirilmiş metin oluşturuyoruz
        # Konu, başlık ve içeriği birleştirerek daha iyi eşleşme sağlıyoruz
        search_text = f"{item['subject']} {item['topic']}: {item['content']}"
        
        # Vektör oluştur
        vector = model.encode(search_text)
        
        # FAISS'e ekle (Senin VectorIndex.add metodun memory_id bekliyor)
        # Burada her chunk için benzersiz bir sayısal ID veriyoruz (i)
        v_index.add(vector, memory_id=i)
        
        if i % 5 == 0:
            print(f">>> {i} adet veri işlendi...")

    print(">>> [BAŞARILI] Veriler FAISS'e gömüldü!")

if __name__ == "__main__":
    start_ingest()
