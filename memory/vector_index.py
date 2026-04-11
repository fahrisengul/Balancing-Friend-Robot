# memory/vector_index.py

import os
import json
import faiss
import numpy as np


INDEX_PATH = "memory/faiss.index"
META_PATH = "memory/faiss_meta.json"
VECTOR_DIM = 384


class VectorIndex:
    def __init__(self, dim=VECTOR_DIM):
        self.dim = dim
        self.index = None
        self.meta = []
        self._load()

    def _load(self):
        if os.path.exists(INDEX_PATH):
            self.index = faiss.read_index(INDEX_PATH)
        else:
            self.index = faiss.IndexFlatIP(self.dim)

        if os.path.exists(META_PATH):
            with open(META_PATH, "r", encoding="utf-8") as f:
                self.meta = json.load(f)
        else:
            self.meta = []

    def _save(self):
        faiss.write_index(self.index, INDEX_PATH)
        with open(META_PATH, "w", encoding="utf-8") as f:
            json.dump(self.meta, f, ensure_ascii=False, indent=2)

    def add(self, vector: np.ndarray, memory_id: int):
        if memory_id is None:
            raise ValueError("memory_id boş olamaz")

        vector = np.asarray([vector], dtype="float32")
        self.index.add(vector)
        self.meta.append({"memory_id": int(memory_id)})
        self._save()

        print(f">>> [FAISS] memory_id={memory_id} eklendi | total={self.index.ntotal}")

    def search(self, vector: np.ndarray, k=3):
        if self.index.ntotal == 0:
            return []

        vector = np.asarray([vector], dtype="float32")
        scores, idxs = self.index.search(vector, k)

        results = []
        for pos, score in zip(idxs[0], scores[0]):
            if pos == -1:
                continue
            if pos >= len(self.meta):
                continue

            memory_id = self.meta[pos]["memory_id"]
            results.append({
                "memory_id": memory_id,
                "score": float(score),
            })

        return results

    def total(self):
        return self.index.ntotal if self.index is not None else 0
