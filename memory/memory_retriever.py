from .embedder import Embedder
from .vector_index import VectorIndex


class MemoryRetriever:
    def __init__(self, memory_manager):
        self.memory = memory_manager
        self.embedder = Embedder()
        self.index = VectorIndex()

        # cosine benzeri normalized IP skor eşiği
        self.min_score = 0.42
        self.max_memories = 2

    def get_context(self, text: str) -> str:
        parts = []

        name = self._get_name()
        if name:
            parts.append(f"Kullanıcının adı {name}.")

        memory_items = self._vector_search(text)

        if not memory_items:
            memory_items = self._fallback_search(text)

        if memory_items:
            parts.append("İlgili geçmiş bilgiler:")
            for m in memory_items[: self.max_memories]:
                parts.append(f"- {m}")

        context = "\n".join(parts).strip()
        print(f">>> [RAG CONTEXT] {context if context else 'YOK'}")
        return context

    # =========================================================
    # PROFILE
    # =========================================================
    def _get_name(self):
        try:
            p = self.memory.get_person_by_role("tanem")
            if p and p.get("name"):
                return p["name"]
        except Exception:
            pass
        return None

    # =========================================================
    # VECTOR SEARCH
    # =========================================================
    def _vector_search(self, text):
        try:
            if self.index.total() == 0:
                return []

            vec = self.embedder.embed(text)
            results = self.index.search(vec, k=5)

            filtered = []
            seen = set()

            for item in results:
                score = item["score"]
                memory_id = item["memory_id"]

                if score < self.min_score:
                    continue

                memory_text = self.memory.get_memory_by_id(memory_id)
                if not memory_text:
                    continue

                key = self._normalize(memory_text)
                if key in seen:
                    continue

                # query ile çok alakasız görünüyorsa alma
                if not self._is_relevant(text, memory_text):
                    continue

                seen.add(key)
                filtered.append(memory_text)

                if len(filtered) >= self.max_memories:
                    break

            return filtered

        except Exception as e:
            print(f">>> [VECTOR SEARCH ERROR] {e}")
            return []

    # =========================================================
    # FALLBACK
    # =========================================================
    def _fallback_search(self, text):
        try:
            raw = self.memory.search_memories(text, limit=5)
            filtered = []

            for m in raw:
                if self._is_relevant(text, m):
                    filtered.append(m)
                if len(filtered) >= self.max_memories:
                    break

            return filtered
        except Exception:
            return []

    # =========================================================
    # RELEVANCE
    # =========================================================
    def _is_relevant(self, query: str, memory_text: str) -> bool:
        q = self._normalize(query)
        m = self._normalize(memory_text)

        q_tokens = set(q.split())
        m_tokens = set(m.split())

        if not q_tokens or not m_tokens:
            return False

        overlap = len(q_tokens.intersection(m_tokens))

        # doğrudan ortak token varsa kabul
        if overlap >= 1:
            return True

        # eğitim kelimeleri için yumuşak eşleştirme
        school_terms = {
            "sinav", "stres", "lgs", "okul", "ders", "odev", "kaygi"
        }
        if (q_tokens & school_terms) and (m_tokens & school_terms):
            return True

        return False

    def _normalize(self, text: str) -> str:
        t = (text or "").lower().strip()
        t = (
            t.replace("ı", "i")
            .replace("ğ", "g")
            .replace("ş", "s")
            .replace("ç", "c")
            .replace("ö", "o")
            .replace("ü", "u")
        )

        import re
        t = re.sub(r"[^a-z0-9\s]", " ", t)
        t = re.sub(r"\s+", " ", t).strip()
        return t
