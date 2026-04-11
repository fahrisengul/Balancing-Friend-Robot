# memory/embedder.py
from sentence_transformers import SentenceTransformer


class Embedder:
    def __init__(self):
        self.model = SentenceTransformer(
            "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
        )

    def embed(self, text: str):
        return self.model.encode(text, normalize_embeddings=True)
