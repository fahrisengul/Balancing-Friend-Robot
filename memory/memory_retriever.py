# memory/memory_retriever.py

from .embedder import Embedder
from .vector_index import VectorIndex


class MemoryRetriever:
    def __init__(self, memory_manager):
        self.memory = memory_manager
        self.embedder = Embedder()
        self.index = VectorIndex()

    def get_context(self, text: str) -> str:
        parts = []

        # name
        name = self._get_name()
        if name:
            parts.append(f"Kullanıcının adı {name}.")

        # vector search
        memories = self._vector_search(text)

        if memories:
            parts.append("İlgili geçmiş bilgiler:")
            for m in memories:
                parts.append(f"- {m}")

        return "\n".join(parts)

    # -----------------------
    def _vector_search(self, text):
        try:
            vec = self.embedder.embed(text)
            ids, scores = self.index.search(vec, k=3)

            results = []
            for i in ids:
                if i == -1:
                    continue

                m = self.memory.get_memory_by_id(i)
                if m:
                    results.append(m)

            return results

        except Exception as e:
            print(f">>> [VECTOR SEARCH ERROR] {e}")
            return []

    # -----------------------
    def _get_name(self):
        if hasattr(self.memory, "get_person_by_role"):
            p = self.memory.get_person_by_role("tanem")
            if p and p.get("name"):
                return p["name"]
        return None
