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

        name = self._get_name()
        if name:
            parts.append(f"Kullanıcının adı {name}.")

        memories = self._vector_search(text)

        if not memories:
            memories = self._fallback_search(text)

        if memories:
            parts.append("İlgili geçmiş bilgiler:")
            for m in memories[:3]:
                parts.append(f"- {m}")

        context = "\n".join(parts).strip()
        print(f">>> [RAG CONTEXT] {context if context else 'YOK'}")
        return context

    def _get_name(self):
        try:
            p = self.memory.get_person_by_role("tanem")
            if p and p.get("name"):
                return p["name"]
        except Exception:
            pass
        return None

    def _vector_search(self, text):
        try:
            if self.index.total() == 0:
                return []

            vec = self.embedder.embed(text)
            results = self.index.search(vec, k=3)

            memories = []
            for item in results:
                memory_id = item["memory_id"]
                memory_text = self.memory.get_memory_by_id(memory_id)
                if memory_text:
                    memories.append(memory_text)

            return memories

        except Exception as e:
            print(f">>> [VECTOR SEARCH ERROR] {e}")
            return []

    def _fallback_search(self, text):
        try:
            return self.memory.search_memories(text, limit=3)
        except Exception:
            return []
