# memory/memory_retriever.py

from memory.embedder import Embedder
from memory.vector_index import VectorIndex


class MemoryRetriever:
    def __init__(self, memory_manager):
        self.mm = memory_manager
        self.embedder = Embedder()
        self.vector = VectorIndex()

    def get_context(self, query: str):
        query = query.lower()

        recent = self._get_recent()
        keyword = self._get_keyword(query)
        semantic = self._get_vector(query)
        profile = self._get_profile()

        return self._build(recent, keyword, semantic, profile)

    def _get_recent(self):
        try:
            rows = self.mm.get_recent_memories(3)
            return [r["content"] for r in rows]
        except:
            return []

    def _get_keyword(self, query):
        try:
            rows = self.mm.search_memories_by_keyword(query, 3)
            return [r["content"] for r in rows]
        except:
            return []

    def _get_vector(self, query):
        try:
            vec = self.embedder.embed(query)
            results = self.vector.search(vec, 3)
            return [r["content"] for r in results]
        except:
            return []

    def _get_profile(self):
        try:
            profile = self.mm.get_person_profile()
            parts = []

            if profile.get("likes"):
                parts.append(f"Sevdiği şeyler: {profile['likes']}")

            if profile.get("difficulties"):
                parts.append(f"Zorlandığı konular: {profile['difficulties']}")

            return parts
        except:
            return []

    def _build(self, recent, keyword, semantic, profile):
        context_parts = []

        if profile:
            context_parts.append("Kullanıcı:\n- " + "\n- ".join(profile))

        if recent:
            context_parts.append("Son:\n- " + "\n- ".join(recent))

        if keyword:
            context_parts.append("Anahtar eşleşme:\n- " + "\n- ".join(keyword))

        if semantic:
            context_parts.append("Benzer geçmiş:\n- " + "\n- ".join(semantic))

        return "\n\n".join(context_parts)
