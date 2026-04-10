# memory/memory_retriever.py

import time


class MemoryRetriever:
    def __init__(self, memory_manager):
        self.mm = memory_manager

    # -----------------------------
    # MAIN ENTRY
    # -----------------------------
    def get_context(self, query: str):
        query = query.lower()

        recent = self._get_recent_memories()
        relevant = self._get_relevant_memories(query)
        profile = self._get_profile_summary()

        return self._build_context(recent, relevant, profile)

    # -----------------------------
    # RECENT MEMORIES
    # -----------------------------
    def _get_recent_memories(self, limit=3):
        try:
            rows = self.mm.get_recent_memories(limit)
            return [r["content"] for r in rows]
        except:
            return []

    # -----------------------------
    # RELEVANT MEMORIES
    # -----------------------------
    def _get_relevant_memories(self, query, limit=3):
        try:
            rows = self.mm.search_memories_by_keyword(query, limit)
            return [r["content"] for r in rows]
        except:
            return []

    # -----------------------------
    # PROFILE SUMMARY
    # -----------------------------
    def _get_profile_summary(self):
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

    # -----------------------------
    # CONTEXT BUILDER
    # -----------------------------
    def _build_context(self, recent, relevant, profile):
        context_parts = []

        if profile:
            context_parts.append("Kullanıcı hakkında:\n- " + "\n- ".join(profile))

        if recent:
            context_parts.append("Son konuşmalar:\n- " + "\n- ".join(recent))

        if relevant:
            context_parts.append("İlgili geçmiş:\n- " + "\n- ".join(relevant))

        return "\n\n".join(context_parts)
