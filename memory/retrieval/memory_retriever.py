class MemoryRetriever:
    def __init__(self, memory_manager, faiss_adapter):
        self.memory = memory_manager
        self.faiss = faiss_adapter

    def get_context_bundle(self, text: str, intent: str, mode: str, top_k: int = 5):
        try:
            results = self.faiss.search(text, top_k=top_k) or []
        except Exception:
            results = []

        selected_chunks = []
        context_parts = []

        for r in results:
            content = r.get("content") or ""
            if content:
                context_parts.append(content)
                selected_chunks.append({
                    "id": r.get("id"),
                    "score": r.get("score"),
                })

        context_text = "\n".join(context_parts).strip()

        confidence = min(1.0, 0.4 + 0.1 * len(selected_chunks)) if selected_chunks else 0.0

        return {
            "context_text": context_text,
            "selected_chunks": selected_chunks,
            "confidence": confidence,
            "source": "faiss" if selected_chunks else "none",
            "query_variants": [text],
            "reranked_preview": selected_chunks[:5],
        }
