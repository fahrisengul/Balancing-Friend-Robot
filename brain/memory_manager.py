import os
import json
import re
from datetime import datetime
from typing import List, Dict, Any


class MemoryManager:
    def __init__(self, memory_path: str = "memory_store.json"):
        self.memory_path = memory_path
        self.memories = self._load_memories()

    # ---------------------------------------------------------
    # IO
    # ---------------------------------------------------------
    def _load_memories(self) -> List[Dict[str, Any]]:
        if not os.path.exists(self.memory_path):
            return []

        try:
            with open(self.memory_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                return data
            return []
        except Exception:
            return []

    def _save_memories(self):
        with open(self.memory_path, "w", encoding="utf-8") as f:
            json.dump(self.memories, f, ensure_ascii=False, indent=2)

    # ---------------------------------------------------------
    # PUBLIC WRITE API
    # ---------------------------------------------------------
    def add_memory(
        self,
        text: str,
        category: str = "general",
        priority: int = 1,
        tags: List[str] | None = None,
        source: str = "conversation",
    ):
        text = (text or "").strip()
        if not text:
            return

        record = {
            "text": text,
            "category": category,
            "priority": int(priority),
            "tags": tags or [],
            "source": source,
            "created_at": datetime.utcnow().isoformat(),
        }
        self.memories.append(record)
        self._save_memories()

    # ---------------------------------------------------------
    # PUBLIC READ API
    # ---------------------------------------------------------
    def search_memories(self, query: str, limit: int = 5) -> List[str]:
        query_norm = self._normalize(query)
        if not query_norm:
            return []

        query_tokens = set(query_norm.split())
        scored = []

        for mem in self.memories:
            mem_text = mem.get("text", "")
            mem_cat = mem.get("category", "general")
            mem_tags = mem.get("tags", [])
            mem_priority = int(mem.get("priority", 1))

            mem_norm = self._normalize(mem_text)
            if not mem_norm:
                continue

            mem_tokens = set(mem_norm.split())
            overlap = len(query_tokens.intersection(mem_tokens))

            score = 0

            # Ana lexical overlap
            score += overlap * 3

            # Tag overlap
            for tag in mem_tags:
                tag_norm = self._normalize(tag)
                if tag_norm and tag_norm in query_norm:
                    score += 2

            # Kategori bonusları
            if mem_cat == "identity":
                score += 1
            elif mem_cat == "preference":
                score += 1
            elif mem_cat == "milestone":
                score += 1

            # Priority bonus
            score += min(mem_priority, 3)

            # Repetitive persona bilgilerini baskıla
            repetitive_terms = ["dogum gunu", "30 mayis", "voleybol", "robot kulubu"]
            if any(rt in mem_norm for rt in repetitive_terms):
                if not any(rt in query_norm for rt in repetitive_terms):
                    score -= 4

            # Alakasız ama yüksek öncelikli memory spam'ini engelle
            if overlap == 0 and score < 4:
                continue

            if score > 0:
                scored.append((score, mem_text))

        scored.sort(key=lambda x: x[0], reverse=True)

        # Tekrarları temizle
        unique = []
        seen = set()
        for score, text in scored:
            key = self._normalize(text)
            if key not in seen:
                unique.append(text)
                seen.add(key)
            if len(unique) >= limit:
                break

        return unique

    # ---------------------------------------------------------
    # OPTIONAL HELPERS
    # ---------------------------------------------------------
    def seed_default_memories(self):
        """
        İstersen bir kez çalıştırıp temel hafızaları yükleyebilirsin.
        """
        if self.memories:
            return

        self.add_memory(
            "Tanem ile sıcak, kısa ve doğal şekilde konuşulmalı.",
            category="interaction_rule",
            priority=3,
            tags=["iletişim", "doğal konuşma"]
        )
        self.add_memory(
            "Tanem'in doğum günü 30 Mayıs.",
            category="milestone",
            priority=2,
            tags=["doğum günü", "30 mayıs"]
        )
        self.add_memory(
            "Tanem voleybol ile ilgileniyor.",
            category="interest",
            priority=1,
            tags=["voleybol", "spor"]
        )
        self.add_memory(
            "Robot kulübü Tanem için önemli bir konu olabilir.",
            category="interest",
            priority=1,
            tags=["robot kulübü", "proje"]
        )

    # ---------------------------------------------------------
    # UTILS
    # ---------------------------------------------------------
    def _normalize(self, text: str) -> str:
        t = text.lower().strip()
        t = (
            t.replace("ı", "i")
             .replace("ğ", "g")
             .replace("ş", "s")
             .replace("ç", "c")
             .replace("ö", "o")
             .replace("ü", "u")
        )
        t = re.sub(r"[^a-z0-9\s]", " ", t)
        t = re.sub(r"\s+", " ", t).strip()
        return t
