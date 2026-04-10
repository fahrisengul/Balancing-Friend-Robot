# memory/embedder.py

from sentence_transformers import SentenceTransformer
import numpy as np


class Embedder:
    def __init__(self):
        self.model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")

    def embed(self, text: str) -> np.ndarray:
        if not text:
            return None
        vec = self.model.encode([text])[0]
        return vec.astype("float32")
