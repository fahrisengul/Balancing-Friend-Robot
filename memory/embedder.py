# memory/embedder.py
from sentence_transformers import SentenceTransformer
import numpy as np


class Embedder:
    def __init__(self):
        self.model = SentenceTransformer(
            "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
        )

    def embed(self, text: str) -> np.ndarray:
        text = (text or "").strip()
        if not text:
            raise ValueError("embed için text boş olamaz")

        vec = self.model.encode(text, normalize_embeddings=True)
        return np.asarray(vec, dtype="float32")
