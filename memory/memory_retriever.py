from typing import Any, Dict, List, Optional

from .faiss_adapter import FaissAdapter


class MemoryRetriever:
    def __init__(self, memory_manager, faiss_adapter: Optional[FaissAdapter] = None):
        self.memory = memory_manager
        self.faiss = faiss_adapter or FaissAdapter()

    def get_context(self, text: str, intent: str = "general", mode: str = "general", top_k: int = 4) -> str:
        bundle = self.get_context_bundle(text=text, intent=intent, mode=mode, top_k=top_k)
        return bundle["context_text"]

    def get_context_bundle(
        self,
        text: str,
        intent: str = "general",
        mode: str = "general",
        top_k: int = 4,
    ) -> Dict[str, Any]:
        query = self._normalize(text)

        if not query:
            return self._empty_bundle()

        if mode != "education":
            memories = self._build_memory_context(query)
            return {
                "context_text": memories,
                "selected_chunks": [],
                "confidence": 0.20 if memories else 0.0,
                "source": "memory_only",
            }

        candidates = self._search_candidates(query, intent=intent)
        reranked = self._rerank_candidates(query=query, intent=intent, candidates=candidates)
        selected = self._select_diverse_chunks(reranked, limit=top_k)
        context_text = self._assemble_context(selected)
        confidence = self._estimate_confidence(selected)

        return {
            "context_text": context_text,
            "selected_chunks": selected,
            "confidence": confidence,
            "source": "faiss_rag_v2" if selected else "none",
        }

    def _search_candidates(self, query: str, intent: str) -> List[Dict[str, Any]]:
        filters = None

        # İstersen burada subject / grade gibi filtreler de ileride eklenebilir.
        return self.faiss.search(query=query, top_k=12, filters=filters)

    def _rerank_candidates(
        self,
        query: str,
        intent: str,
        candidates: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        reranked: List[Dict[str, Any]] = []

        for item in candidates:
            base_score = float(item.get("score", 0.0))
            chunk_type = item.get("chunk_type", "")
            topic = self._normalize(item.get("topic", ""))
            content = self._normalize(item.get("content", ""))
            keywords = " ".join(item.get("keywords", []))
            keywords = self._normalize(keywords)
            intent_tags = " ".join(item.get("intent_tags", []))
            intent_tags = self._normalize(intent_tags)
            priority = float(item.get("embedding_priority", 0.0))

            final_score = base_score
            final_score += self._intent_bonus(intent, chunk_type)
            final_score += self._topic_bonus(query, topic, content, keywords)
            final_score += self._intent_tag_bonus(query, intent, intent_tags)
            final_score += priority * 0.15

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
                "example": 0.18,
                "common_mistake": 0.12,
                "relation": 0.08,
            },
            "education_topics": {
                "curriculum": 0.35,
                "definition": 0.20,
                "relation": 0.12,
                "exam_guidance": 0.10,
                "simple_explanation": 0.08,
            },
            "exam_support": {
                "exam_strategy": 0.32,
                "exam_guidance": 0.28,
                "study_tip": 0.24,
                "common_mistake": 0.12,
                "simple_explanation": 0.08,
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

    def _intent_tag_bonus(self, query: str, intent: str, intent_tags: str) -> float:
        bonus = 0.0

        if not intent_tags:
            return 0.0

        if intent == "concept_explanation" and ("tanim" in intent_tags or "nedir" in intent_tags):
            bonus += 0.12

        if intent == "education_topics" and ("konu" in query or "liste" in query):
            if "konu" in intent_tags or "liste" in intent_tags:
                bonus += 0.12

        if intent == "exam_support" and ("strateji" in intent_tags or "taktik" in intent_tags):
            bonus += 0.12

        return bonus

    def _select_diverse_chunks(self, items: List[Dict[str, Any]], limit: int = 4) -> List[Dict[str, Any]]:
        selected: List[Dict[str, Any]] = []
        used_topic_type = set()
        used_topics = {}

        for item in items:
            topic = item.get("topic", "")
            chunk_type = item.get("chunk_type", "")
            pair = (topic, chunk_type)

            if pair in used_topic_type:
                continue

            if used_topics.get(topic, 0) >= 2:
                continue

            selected.append(item)
            used_topic_type.add(pair)
            used_topics[topic] = used_topics.get(topic, 0) + 1

            if len(selected) >= limit:
                break

        return selected

    def _assemble_context(self, items: List[Dict[str, Any]]) -> str:
        if not items:
            return ""

        ordered = sorted(items, key=lambda x: x.get("final_score", 0.0), reverse=True)

        parts = []
        for item in ordered:
            topic = item.get("topic", "")
            chunk_type = item.get("chunk_type", "")
            content = (item.get("content") or "").strip()
            if not content:
                continue

            parts.append(f"[Konu: {topic} | Tip: {chunk_type}] {content}")

        return "\n".join(parts).strip()

    def _estimate_confidence(self, items: List[Dict[str, Any]]) -> float:
        if not items:
            return 0.0

        scores = [float(i.get("final_score", 0.0)) for i in items]
        avg_score = sum(scores) / len(scores)

        # normalize edilmiş yaklaşık bir confidence
        if avg_score >= 1.20:
            return 0.90
        if avg_score >= 0.95:
            return 0.78
        if avg_score >= 0.75:
            return 0.65
        if avg_score >= 0.55:
            return 0.48
        return 0.30

    def _build_memory_context(self, query: str) -> str:
        try:
            rows = self.memory.search_memories(query, limit=3)
            if isinstance(rows, list):
                return "\n".join(str(r) for r in rows if r).strip()
            if isinstance(rows, str):
                return rows.strip()
            return ""
        except Exception:
            return ""

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
