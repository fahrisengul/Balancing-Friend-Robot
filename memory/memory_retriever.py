from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


class MemoryRetriever:
    def __init__(self, memory_manager, faiss_adapter):
        self.memory = memory_manager
        self.faiss = faiss_adapter

        self.short_term_weight = 1.35
        self.long_term_weight = 1.00

        self.default_search_k = 10
        self.max_context_chars = 2600

    # =========================================================
    # PUBLIC API
    # =========================================================
    def get_context(
        self,
        text: str,
        intent: str = "general",
        mode: str = "general",
        top_k: int = 5,
    ) -> str:
        bundle = self.get_context_bundle(
            text=text,
            intent=intent,
            mode=mode,
            top_k=top_k,
        )
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

        query_bundle = self._build_query_bundle(text=text, intent=intent, mode=mode)

        raw_hits = self._multi_index_search(
            query_variants=query_bundle["query_variants"],
            top_k=max(self.default_search_k, top_k * 2),
        )

        if not raw_hits:
            return self._empty_bundle()

        merged_hits = self._dedupe_hits(raw_hits)
        reranked_hits = self._rerank(
            original_text=text,
            normalized_query=query,
            intent=intent,
            mode=mode,
            items=merged_hits,
            query_bundle=query_bundle,
        )

        selected = self._select_diverse(reranked_hits, limit=top_k)
        context_text = self._assemble_context(selected)
        confidence = self._estimate_confidence(selected)

        reranked_preview = [
            {
                "id": x.get("id"),
                "topic": x.get("topic"),
                "chunk_type": x.get("chunk_type"),
                "memory_scope": x.get("memory_scope"),
                "score": x.get("score"),
                "final_score": x.get("final_score"),
            }
            for x in reranked_hits[:8]
        ]

        return {
            "context_text": context_text,
            "selected_chunks": selected,
            "confidence": confidence,
            "source": "multi_index_rag_v2" if selected else "none",
            "query_variants": query_bundle.get("query_variants", []),
            "reranked_preview": reranked_preview,
        }

    # =========================================================
    # QUERY BUILD
    # =========================================================
    def _build_query_bundle(self, text: str, intent: str, mode: str) -> Dict[str, Any]:
        raw = (text or "").strip()
        norm = self._normalize(raw)
        tokens = [tok for tok in norm.split() if len(tok) > 2]

        topic_hints = self._extract_topic_hints(norm)
        query_variants: List[str] = []

        query_variants.append(norm)

        if len(tokens) >= 2:
            query_variants.append(" ".join(tokens[: min(6, len(tokens))]))

        if topic_hints:
            query_variants.append(" ".join(topic_hints))

        intent_phrase = self._intent_query_hint(intent=intent, mode=mode)
        if intent_phrase:
            if topic_hints:
                query_variants.append(f"{' '.join(topic_hints)} {intent_phrase}".strip())
            else:
                query_variants.append(f"{norm} {intent_phrase}".strip())

        clean_variants = []
        seen = set()
        for q in query_variants:
            qn = self._normalize(q)
            if qn and qn not in seen:
                seen.add(qn)
                clean_variants.append(qn)

        return {
            "query_variants": clean_variants[:4],
            "topic_hints": topic_hints,
            "tokens": tokens,
        }

    def _intent_query_hint(self, intent: str, mode: str) -> str:
        mapping = {
            "education_topics": "konu basliklari mufredat",
            "concept_explanation": "tanim aciklama ornek",
            "exam_support": "sinav strateji calisma onerisi yaygin hata",
            "follow_up": "devam detay ornek",
        }
        return mapping.get(intent, "egitim" if mode == "education" else "")

    def _extract_topic_hints(self, query: str) -> List[str]:
        known = [
            "lgs",
            "dgs",
            "matematik",
            "turkce",
            "fen",
            "ingilizce",
            "din",
            "inkilap",
            "geometri",
            "cebir",
            "veri analizi",
            "uslu sayilar",
            "karekok",
            "carpanlar ve katlar",
            "cebirsel ifadeler",
            "esitsizlik",
            "olasilik",
        ]

        hits = []
        for k in known:
            if k in query:
                hits.append(k)

        if not hits:
            tokens = [tok for tok in query.split() if len(tok) > 3]
            hits.extend(tokens[:3])

        return hits[:4]

    # =========================================================
    # SEARCH
    # =========================================================
    def _multi_index_search(self, query_variants: List[str], top_k: int) -> List[Dict[str, Any]]:
        all_hits: List[Dict[str, Any]] = []

        for idx, query in enumerate(query_variants):
            short_hits = self.faiss.search_short_term(query, top_k=top_k)
            long_hits = self.faiss.search_long_term(query, top_k=top_k)

            for item in short_hits:
                x = dict(item)
                x["memory_scope"] = "short_term"
                x["query_variant"] = query
                x["variant_rank"] = idx
                all_hits.append(x)

            for item in long_hits:
                x = dict(item)
                x["memory_scope"] = "long_term"
                x["query_variant"] = query
                x["variant_rank"] = idx
                all_hits.append(x)

        return all_hits

    def _dedupe_hits(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        best_by_key: Dict[str, Dict[str, Any]] = {}

        for item in items:
            key = self._hit_key(item)
            prev = best_by_key.get(key)

            if prev is None:
                best_by_key[key] = item
                continue

            prev_score = float(prev.get("score", 0.0))
            curr_score = float(item.get("score", 0.0))

            if curr_score > prev_score:
                best_by_key[key] = item

        return list(best_by_key.values())

    def _hit_key(self, item: Dict[str, Any]) -> str:
        if item.get("id"):
            return f"id::{item['id']}"
        content = self._normalize(item.get("content", ""))
        topic = self._normalize(item.get("topic", ""))
        return f"content::{topic}::{content[:200]}"

    # =========================================================
    # RERANK
    # =========================================================
    def _rerank(
        self,
        original_text: str,
        normalized_query: str,
        intent: str,
        mode: str,
        items: List[Dict[str, Any]],
        query_bundle: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        reranked: List[Dict[str, Any]] = []
        query_tokens = set(query_bundle.get("tokens", []))
        topic_hints = query_bundle.get("topic_hints", [])

        for item in items:
            base_score = float(item.get("score", 0.0))
            scope = item.get("memory_scope", "long_term")
            chunk_type = item.get("chunk_type", "")
            source_type = item.get("source_type", "")
            subject = self._normalize(item.get("subject", ""))
            topic = self._normalize(item.get("topic", ""))
            title = self._normalize(item.get("title", ""))
            content = self._normalize(item.get("content", ""))
            keywords = " ".join(item.get("keywords", []))
            keywords = self._normalize(keywords)
            intent_tags = " ".join(item.get("intent_tags", []))
            intent_tags = self._normalize(intent_tags)
            priority = float(item.get("embedding_priority", 0.0))
            variant_rank = int(item.get("variant_rank", 0))

            final_score = 0.0

            final_score += self._normalize_similarity(base_score)

            if scope == "short_term":
                final_score *= self.short_term_weight
            else:
                final_score *= self.long_term_weight

            final_score += self._intent_bonus(intent, chunk_type)
            final_score += self._mode_source_bonus(mode, source_type, subject)
            final_score += self._topic_bonus(query_tokens, topic_hints, topic, title, keywords, content)

            if intent and intent in intent_tags:
                final_score += 0.08

            final_score += priority * 0.12
            final_score += self._recency_bonus(item.get("created_at"))
            final_score += max(0.0, 0.06 - (variant_rank * 0.02))

            enriched = dict(item)
            enriched["final_score"] = round(final_score, 6)
            reranked.append(enriched)

        reranked.sort(key=lambda x: x["final_score"], reverse=True)
        return reranked

    def _normalize_similarity(self, score: float) -> float:
        if score <= 0:
            return 0.0
        if score >= 0.95:
            return 1.00
        if score >= 0.85:
            return 0.90
        if score >= 0.75:
            return 0.78
        if score >= 0.65:
            return 0.66
        if score >= 0.55:
            return 0.55
        return max(0.0, score * 0.85)

    def _intent_bonus(self, intent: str, chunk_type: str) -> float:
        weights = {
            "concept_explanation": {
                "definition": 0.34,
                "simple_explanation": 0.28,
                "example": 0.20,
                "relation": 0.10,
                "common_mistake": 0.08,
            },
            "education_topics": {
                "curriculum": 0.34,
                "exam_guidance": 0.22,
                "definition": 0.16,
                "relation": 0.10,
                "simple_explanation": 0.06,
            },
            "exam_support": {
                "exam_strategy": 0.34,
                "exam_guidance": 0.26,
                "study_tip": 0.23,
                "common_mistake": 0.14,
                "example": 0.08,
            },
            "follow_up": {
                "simple_explanation": 0.20,
                "example": 0.18,
                "study_tip": 0.16,
                "relation": 0.12,
                "exam_strategy": 0.12,
            },
        }
        return weights.get(intent, {}).get(chunk_type, 0.0)

    def _mode_source_bonus(self, mode: str, source_type: str, subject: str) -> float:
        bonus = 0.0

        if mode == "education":
            if source_type == "meb_aligned":
                bonus += 0.16
            elif source_type == "gemini_generated":
                bonus += 0.08

            if subject:
                bonus += 0.05

        return bonus

    def _topic_bonus(
        self,
        query_tokens: set,
        topic_hints: List[str],
        topic: str,
        title: str,
        keywords: str,
        content: str,
    ) -> float:
        bonus = 0.0

        for hint in topic_hints:
            hint_n = self._normalize(hint)
            if hint_n and hint_n in topic:
                bonus += 0.18
            elif hint_n and hint_n in title:
                bonus += 0.10

        if topic and any(tok in topic for tok in query_tokens):
            bonus += 0.16

        if title and any(tok in title for tok in query_tokens):
            bonus += 0.12

        if keywords and any(tok in keywords for tok in query_tokens):
            bonus += 0.10

        content_hits = sum(1 for tok in query_tokens if len(tok) > 3 and tok in content)
        bonus += min(0.10, content_hits * 0.03)

        return bonus

    def _recency_bonus(self, created_at: Optional[str]) -> float:
        if not created_at:
            return 0.0

        try:
            dt = self._parse_dt(created_at)
            if dt is None:
                return 0.0

            now = datetime.now(timezone.utc)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)

            age_hours = (now - dt).total_seconds() / 3600.0

            if age_hours <= 1:
                return 0.18
            if age_hours <= 24:
                return 0.12
            if age_hours <= 24 * 7:
                return 0.06
            return 0.0
        except Exception:
            return 0.0

    def _parse_dt(self, value: str) -> Optional[datetime]:
        raw = (value or "").strip()
        if not raw:
            return None

        try:
            return datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except Exception:
            return None

    # =========================================================
    # DIVERSITY / CONTEXT
    # =========================================================
    def _select_diverse(self, items: List[Dict[str, Any]], limit: int = 5) -> List[Dict[str, Any]]:
        selected: List[Dict[str, Any]] = []
        used_pairs = set()
        topic_count: Dict[str, int] = {}

        short_best = None
        for item in items:
            if item.get("memory_scope") == "short_term":
                short_best = item
                break

        if short_best:
            selected.append(short_best)
            used_pairs.add((short_best.get("topic", ""), short_best.get("chunk_type", "")))
            topic = short_best.get("topic", "")
            topic_count[topic] = 1

        for item in items:
            if len(selected) >= limit:
                break

            topic = item.get("topic", "")
            chunk_type = item.get("chunk_type", "")
            pair = (topic, chunk_type)

            if pair in used_pairs:
                continue

            if topic_count.get(topic, 0) >= 2:
                continue

            if self._too_similar_to_selected(item, selected):
                continue

            selected.append(item)
            used_pairs.add(pair)
            topic_count[topic] = topic_count.get(topic, 0) + 1

        return selected[:limit]

    def _too_similar_to_selected(self, item: Dict[str, Any], selected: List[Dict[str, Any]]) -> bool:
        item_content = self._normalize(item.get("content", ""))
        item_topic = self._normalize(item.get("topic", ""))

        for s in selected:
            s_content = self._normalize(s.get("content", ""))
            s_topic = self._normalize(s.get("topic", ""))

            if item_topic == s_topic and item_content[:160] == s_content[:160]:
                return True

        return False

    def _assemble_context(self, items: List[Dict[str, Any]]) -> str:
        if not items:
            return ""

        parts: List[str] = []
        total_chars = 0

        for idx, item in enumerate(items, start=1):
            scope = item.get("memory_scope", "")
            topic = item.get("topic", "")
            chunk_type = item.get("chunk_type", "")
            source_type = item.get("source_type", "")
            content = (item.get("content") or "").strip()

            if not content:
                continue

            block = (
                f"[{idx}] kaynak={scope}; tip={chunk_type}; konu={topic}; kaynak_tipi={source_type}\n"
                f"{content}"
            )

            projected = total_chars + len(block) + 2
            if projected > self.max_context_chars:
                break

            parts.append(block)
            total_chars = projected

        return "\n\n".join(parts).strip()

    def _estimate_confidence(self, items: List[Dict[str, Any]]) -> float:
        if not items:
            return 0.0

        top_scores = [float(i.get("final_score", 0.0)) for i in items[:3]]
        avg_score = sum(top_scores) / max(1, len(top_scores))

        if avg_score >= 1.30:
            return 0.92
        if avg_score >= 1.08:
            return 0.82
        if avg_score >= 0.88:
            return 0.70
        if avg_score >= 0.68:
            return 0.55
        return 0.35

    # =========================================================
    # HELPERS
    # =========================================================
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

    def _rewrite_query(self, text: str, intent: str, mode: str):
        norm = self._normalize(text)
        tokens = norm.split()
    
        # SQL intent hints
        hints = self.memory.get_intent_hints(intent, mode)
        hint_texts = [h[0] for h in hints]
    
        # SQL topic aliases
        alias_rows = self.memory.get_topic_aliases(tokens)
        topic_hints = [r[0] for r in alias_rows]
    
        queries = [norm]
    
        if topic_hints:
            queries.append(" ".join(topic_hints))
    
        if hint_texts:
            queries.append(f"{norm} {' '.join(hint_texts[:2])}")
    
        return list(set(queries))

    def _extract_topics_from_hits(self, hits):
        topic_counter = {}
    
        for h in hits:
            topic = h.get("topic", "")
            if not topic:
                continue
            topic_counter[topic] = topic_counter.get(topic, 0) + 1
    
        return sorted(topic_counter, key=topic_counter.get, reverse=True)[:3]

    def _refine_query_with_topics(self, base_query, topics):
        if not topics:
            return base_query
    
        return f"{base_query} {' '.join(topics)}"
