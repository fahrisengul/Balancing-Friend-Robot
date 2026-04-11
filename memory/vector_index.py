# memory/vector_index.py

import os
import faiss
import numpy as np


INDEX_PATH = "memory/faiss.index"


class VectorIndex:
    def __init__(self, dim=384):
        self.dim = dim

        if os.path.exists(INDEX_PATH):
            self.index = faiss.read_index(INDEX_PATH)
        else:
            self.index = faiss.IndexFlatIP(dim)

    def add(self, vector):
        vector = np.array([vector]).astype("float32")
        self.index.add(vector)
        self._save()

    def search(self, vector, k=3):
        if self.index.ntotal == 0:
            return [], []

        vector = np.array([vector]).astype("float32")
        scores, ids = self.index.search(vector, k)

        return ids[0], scores[0]

    def _save(self):
        faiss.write_index(self.index, INDEX_PATH)
