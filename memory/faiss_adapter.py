import json
import os
from typing import Any, Dict, List, Optional, Tuple

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer


class FaissAdapter:
    def __init__(
        self,
        embedding_model_name: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        long_index_path: str = "memory/faiss_longterm.index",
        long_meta_path: str = "memory/faiss_longterm_meta.jsonl",
        short_index_path: str = "memory/faiss_shortterm.index",
        short_meta_path: str = "memory/faiss_shortterm_meta.jsonl",
    ):
        self.embedding_model_name = embedding_model_name
        self.long_index_path = long_index_path
        self.long_meta_path = long_meta_path
        self.short_index_path = short_index_path
        self.short_meta_path = short_meta_path

        self.model = None

        self.long_index = None
        self.long_meta_by_vector_id: Dict[int, Dict[str, Any]] = {}

        self.short_index = None
        self.short_meta_by_vector_id: Dict[int, Dict[str, Any]] = {}

        self._load_all()

    # =========================================================
    # LOAD / SAVE
    # =========================================================
    def _lazy_model(self):
        if self.model is None:
            self.model = SentenceTransformer(self.embedding_model_name)

    def _load_all(self):
        self.long_index, self.long_meta_by_vector_id = self._load_index_and_meta(
            self.long_index_path, self.long_meta_path
        )
        self.short_index, self.short_meta_by_vector_id = self._load_index_and_meta(
            self.short_index_path, self.short_meta_path
        )

    def _load_index_and_meta(
        self, index_path: str, meta_path: str
    ) -> Tuple[Optional[faiss.Index], Dict[int, Dict[str, Any]]]:
        index = None
        meta_by_vector_id: Dict[int, Dict[str, Any]] = {}

        if os.path.exists(index_path):
            index = faiss.read_index(index_path)

        if os.path.exists(meta_path):
            with open(meta_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    item = json.loads(line)
                    meta_by_vector_id[int(item["vector_id"])] = item

        return index, meta_by_vector_id

    def save_long_term(self):
        self._save_index_and_meta(
            index=self.long_index,
            meta_by_vector_id=self.long_meta_by_vector_id,
            index_path=self.long_index_path,
            meta_path=self.long_meta_path,
        )

    def save_short_term(self):
        self._save_index_and_meta(
            index=self.short_index,
            meta_by_vector_id=self.short_meta_by_vector_id,
            index_path=self.short_index_path,
            meta_path=self.short_meta_path,
        )

    def _save_index_and_meta(
        self,
        index: Optional[faiss.Index],
        meta_by_vector_id: Dict[int, Dict[str, Any]],
        index_path: str,
        meta_path: str,
    ):
        if index is None:
            return

        os.makedirs(os.path.dirname(index_path), exist_ok=True)
        os.makedirs(os.path.dirname(meta_path), exist_ok=True)

        faiss.write_index(index, index_path)

        with open(meta_path, "w", encoding="utf-8") as f:
            for vector_id in sorted(meta_by_vector_id.keys()):
                f.write(json.dumps(meta_by_vector_id[vector_id], ensure_ascii=False) + "\n")

    # =========================================================
    # STATE
    # =========================================================
    def is_long_ready(self) -> bool:
        return self.long_index is not None and len(self.long_meta_by_vector_id) > 0

    def is_short_ready(self) -> bool:
        return self.short_index is not None and len(self.short_meta_by_vector_id) > 0

    # =========================================================
    # APPEND
    # =========================================================
    def add_long_term(self, items: List[Dict[str, Any]]):
        if not items:
            return

        self._lazy_model()
        vectors = self._embed_items(items)
        self.long_index, self.long_meta_by_vector_id = self._append_to_index(
            index=self.long_index,
            meta_by_vector_id=self.long_meta_by_vector_id,
            items=items,
            vectors=vectors,
        )
        self.save_long_term()

    def add_short_term(self, items: List[Dict[str, Any]]):
        if not items:
            return

        self._lazy_model()
        vectors = self._embed_items(items)
        self.short_index, self.short_meta_by_vector_id = self._append_to_index(
            index=self.short_index,
            meta_by_vector_id=self.short_meta_by_vector_id,
            items=items,
            vectors=vectors,
        )
        self.save_short_term()

    def clear_short_term(self):
        self.short_index = None
        self.short_meta_by_vector_id = {}

        if os.path.exists(self.short_index_path):
            os.remove(self.short_index_path)
        if os.path.exists(self.short_meta_path):
            os.remove(self.short_meta_path)

    def _append_to_index(
        self,
        index: Optional[faiss.Index],
        meta_by_vector_id: Dict[int, Dict[str, Any]],
        items: List[Dict[str, Any]],
        vectors: np.ndarray,
    ) -> Tuple[faiss.Index, Dict[int, Dict[str, Any]]]:
        dim = vectors.shape[1]

        if index is None:
            index = faiss.IndexFlatIP(dim)

        start_id = len(meta_by_vector_id)
        index.add(vectors)

        for offset, item in enumerate(items):
            vector_id = start_id + offset
            record = dict(item)
            record["vector_id"] = vector_id
            meta_by_vector_id[vector_id] = record

        return index, meta_by_vector_id

    def _embed_items(self, items: List[Dict[str, Any]]) -> np.ndarray:
        texts = [str(item.get("content", "")).strip() for item in items]
        vectors = self.model.encode(
            texts,
            normalize_embeddings=True,
            convert_to_numpy=True,
        ).astype("float32")
        return vectors

    # =========================================================
    # SEARCH
    # =========================================================
    def search_long_term(self, query: str, top_k: int = 8) -> List[Dict[str, Any]]:
        return self._search(query, self.long_index, self.long_meta_by_vector_id, top_k)

    def search_short_term(self, query: str, top_k: int = 8) -> List[Dict[str, Any]]:
        return self._search(query, self.short_index, self.short_meta_by_vector_id, top_k)

    def _search(
        self,
        query: str,
        index: Optional[faiss.Index],
        meta_by_vector_id: Dict[int, Dict[str, Any]],
        top_k: int,
    ) -> List[Dict[str, Any]]:
        if not query or index is None or not meta_by_vector_id:
            return []

        self._lazy_model()

        query_vec = self.model.encode(
            [query],
            normalize_embeddings=True,
            convert_to_numpy=True,
        ).astype("float32")

        k = min(top_k, len(meta_by_vector_id))
        scores, ids = index.search(query_vec, k)
        scores = scores[0]
        ids = ids[0]

        results = []
        for score, vector_id in zip(scores, ids):
            if vector_id == -1:
                continue

            meta = meta_by_vector_id.get(int(vector_id))
            if not meta:
                continue

            item = dict(meta)
            item["score"] = float(score)
            results.append(item)

        return results
