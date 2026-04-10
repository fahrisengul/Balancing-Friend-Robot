# memory/vector_index.py

import faiss
import numpy as np
import os
import pickle


class VectorIndex:
    def __init__(self, dim=384, path="memory/vector.index"):
        self.dim = dim
        self.path = path
        self.meta_path = path + ".meta"

        self.index = faiss.IndexFlatL2(dim)
        self.id_map = []

        self._load()

    def add(self, vector: np.ndarray, metadata: dict):
        if vector is None:
            return

        self.index.add(np.array([vector]))
        self.id_map.append(metadata)

        self._save()

    def search(self, vector: np.ndarray, k=3):
        if self.index.ntotal == 0:
            return []

        D, I = self.index.search(np.array([vector]), k)

        results = []
        for idx in I[0]:
            if idx < len(self.id_map):
                results.append(self.id_map[idx])

        return results

    def _save(self):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        faiss.write_index(self.index, self.path)

        with open(self.meta_path, "wb") as f:
            pickle.dump(self.id_map, f)

    def _load(self):
        if os.path.exists(self.path):
            self.index = faiss.read_index(self.path)

        if os.path.exists(self.meta_path):
            with open(self.meta_path, "rb") as f:
                self.id_map = pickle.load(f)
