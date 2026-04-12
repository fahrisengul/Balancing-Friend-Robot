import json
import os
from typing import Any, Dict, List, Optional

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer


class FaissAdapter:
    """
    Basit üretim adaptörü.

    Beklenen dosyalar:
    - memory/faiss.index
    - memory/faiss_meta.jsonl

    faiss_meta.jsonl satır örneği:
    {
      "vector_id": 123,
      "id": "math.exponents.definition.001",
      "subject": "Matematik",
      "topic": "Üslü Sayılar",
      "chunk_type": "definition",
      "content": "...",
      "keywords": ["üs", "taban"],
      "intent_tags": ["nedir", "tanım"],
      "embedding_priority": 1.0
    }
    """

    def __init__(
        self,
        index_path: str = "memory/faiss.index",
        metadata_path: str = "memory/faiss_meta.jsonl",
        embedding_model_name: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
    ):
        self.index_path = index_path
        self.metadata_path = metadata_path
        self.embedding_model_name = embedding_model_name

        self.index = None
        self.model = None
        self.meta_by_vector_id: Dict[int, Dict[str, Any]] = {}

        self._load()

    def _load(self):
        if os.path.exists(self.index_path):
            self.index = faiss.read_index(self.index_path)

        if os.path.exists(self.metadata_path):
            with open(self.metadata_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    item = json.loads(line)
                    vector_id = int(item["vector_id"])
                    self.meta_by_vector_id[vector_id] = item

    def _lazy_model(self):
        if self.model is None:
            self.model = SentenceTransformer(self.embedding_model_name)

    def is_ready(self) -> bool:
        return self.index is not None and len(self.meta_by_vector_id) > 0

    def search(
        self,
        query: str,
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        if not query or not self.is_ready():
            return []

        self._lazy_model()

        query_vec = self.model.encode(
            [query],
            normalize_embeddings=True,
            convert_to_numpy=True,
        ).astype("float32")

        scores, ids = self.index.search(query_vec, top_k * 3)
        scores = scores[0]
        ids = ids[0]

        results: List[Dict[str, Any]] = []

        for score, vector_id in zip(scores, ids):
            if vector_id == -1:
                continue

            meta = self.meta_by_vector_id.get(int(vector_id))
            if not meta:
                continue

            if filters and not self._passes_filters(meta, filters):
                continue

            item = dict(meta)
            item["score"] = float(score)
            results.append(item)

            if len(results) >= top_k:
                break

        return results

    def _passes_filters(self, meta: Dict[str, Any], filters: Dict[str, Any]) -> bool:
        for key, expected in filters.items():
            value = meta.get(key)

            if expected is None:
                continue

            if isinstance(expected, (list, tuple, set)):
                if value not in expected:
                    return False
            else:
                if value != expected:
                    return False

        return True
