from typing import Any, Dict, List, Optional


class MemoryRetriever:
    def __init__(self, memory_manager, faiss_adapter):
        self.memory = memory_manager
        self.faiss = faiss_adapter

    def get_context(self, text: str, intent: str = "general", mode: str = "general", top_k: int = 5) -> str:
        bundle = self.get_context_bundle(text=text, intent=intent, mode=mode, top_k=top_k)
        return bundle["context_text"]

    def get_context_bundle(
        self,
        text: str,
        intent: str = "general",
        mode: str = "general",
        top_k: int = 5,
    ) -> Dict[str, Any]:
        query = self._normalize(text)
        if not query:
            return self._empty_bundle()

        short_hits = self.faiss.search_short_term(query, top_k=8)
        long_hits = self.faiss.search_long_term(query, top_k=8)

        merged = self._merge_hits(short_hits, long_hits)
        reranked = self._rerank(query=query, intent=intent, mode=mode, items=merged)
        selected = self._select_diverse(reranked, limit=top_k)

        context_text = self._assemble_context(selected)
        confidence = self._estimate_confidence(selected)

        return {
            "context_text": context_text,
            "selected_chunks": selected,
            "confidence": confidence,
            "source": "multi_index_rag_v2" if selected else "none",
        }

    def _merge_hits(self, short_hits: List[Dict[str, Any]], long_hits: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        merged = []

        for item in short_hits:
            x = dict(item)
            x["memory_scope"] = "short_term"
            merged.append(x)

        for item in long_hits:
            x = dict(item)
            x["memory_scope"] = "long_term"
            merged.append(x)

        return merged

    def _rerank(
        self,
        query: str,
        intent: str,
        mode: str,
        items: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        reranked: List[Dict[str, Any]] = []

        for item in items:
            base_score = float(item.get("score", 0.0))
            topic = self._normalize(item.get("topic", ""))
            chunk_type = item.get("chunk_type", "")
            content = self._normalize(item.get("content", ""))
            keywords = " ".join(item.get("keywords", []))
            keywords = self._normalize(keywords)
            priority = float(item.get("embedding_priority", 0.0))
            scope = item.get("memory_scope", "long_term")

            final_score = base_score
            final_score += self._intent_bonus(intent, chunk_type)
            final_score += self._topic_bonus(query, topic, content, keywords)
            final_score += priority * 0.15

            # short-term hafıza follow-up için daha değerli
            if scope == "short_term":
                final_score += 0.20

            # education modunda education içeriklerini öne çek
            if mode == "education" and item.get("subject"):
                final_score += 0.05

            enriched = dict(item)
            enriched["final_score"] = round(final_score, 6)
            reranked.append(enriched)

        reranked.sort(key=lambda x: x["final_score"], reverse=True)
        return reranked

    def _intent_bonus(self, intent: str, chunk_type: str) -> float:
        weights = {
            "concept_explanation": {
                "definition": 0.35,
                "simple_explanation": 0.30,
                "example": 0.20,
                "common_mistake": 0.10,
                "relation": 0.08,
            },
            "education_topics": {
                "curriculum": 0.35,
                "definition": 0.20,
                "relation": 0.10,
                "exam_guidance": 0.12,
                "simple_explanation": 0.06,
            },
            "exam_support": {
                "exam_strategy": 0.35,
                "exam_guidance": 0.28,
                "study_tip": 0.25,
                "common_mistake": 0.12,
                "simple_explanation": 0.08,
            },
            "follow_up": {
                "simple_explanation": 0.20,
                "example": 0.18,
                "study_tip": 0.18,
                "exam_strategy": 0.18,
            },
        }
        return weights.get(intent, {}).get(chunk_type, 0.0)

    def _topic_bonus(self, query: str, topic: str, content: str, keywords: str) -> float:
        bonus = 0.0
        query_tokens = set(tok for tok in query.split() if len(tok) > 2)

        if topic and any(tok in topic for tok in query_tokens):
            bonus += 0.22

        if keywords and any(tok in keywords for tok in query_tokens):
            bonus += 0.14

        if content and any(tok in content for tok in query_tokens if len(tok) > 3):
            bonus += 0.08

        return bonus

    def _select_diverse(self, items: List[Dict[str, Any]], limit: int = 5) -> List[Dict[str, Any]]:
        selected = []
        used_pairs = set()
        used_topics = {}

        for item in items:
            topic = item.get("topic", "")
            chunk_type = item.get("chunk_type", "")
            pair = (topic, chunk_type)

            if pair in used_pairs:
                continue

            if used_topics.get(topic, 0) >= 2:
                continue

            selected.append(item)
            used_pairs.add(pair)
            used_topics[topic] = used_topics.get(topic, 0) + 1

            if len(selected) >= limit:
                break

        return selected

    def _assemble_context(self, items: List[Dict[str, Any]]) -> str:
        if not items:
            return ""

        parts = []
        for item in items:
            topic = item.get("topic", "")
            chunk_type = item.get("chunk_type", "")
            scope = item.get("memory_scope", "")
            content = (item.get("content") or "").strip()

            if not content:
                continue

            parts.append(
                f"[Kaynak: {scope} | Konu: {topic} | Tip: {chunk_type}] {content}"
            )

        return "\n".join(parts).strip()

    def _estimate_confidence(self, items: List[Dict[str, Any]]) -> float:
        if not items:
            return 0.0

        scores = [float(i.get("final_score", 0.0)) for i in items]
        avg_score = sum(scores) / len(scores)

        if avg_score >= 1.20:
            return 0.90
        if avg_score >= 0.95:
            return 0.78
        if avg_score >= 0.75:
            return 0.65
        if avg_score >= 0.55:
            return 0.48
        return 0.30

    def _empty_bundle(self) -> Dict[str, Any]:
        return {
            "context_text": "",
            "selected_chunks": [],
            "confidence": 0.0,
            "source": "none",
        }

    def _normalize(self, text: str) -> str:
        t = (text or "").strip().lower()
        return (
            t.replace("ı", "i")
             .replace("ğ", "g")
             .replace("ş", "s")
             .replace("ç", "c")
             .replace("ö", "o")
             .replace("ü", "u")
        )
