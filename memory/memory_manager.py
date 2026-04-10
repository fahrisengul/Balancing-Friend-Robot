import json
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

from .db import get_connection, init_db

import random
return random.choice(templates)


class MemoryManager:
    """
    Sprint 2 v1:
    - profile oku / yaz
    - episodic memory ekle
    - relevant memory ara
    - template çek
    - conversation log yaz
    """

    def __init__(self):
        init_db()

    # =========================================================
    # PERSON PROFILES
    # =========================================================
    def create_person_profile(
        self,
        name: str,
        role: str = "unknown",
        birth_date: Optional[str] = None,
        school_name: Optional[str] = None,
        grade_level: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> int:
        with get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO person_profiles
                (name, role, birth_date, school_name, grade_level, notes, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    name,
                    role,
                    birth_date,
                    school_name,
                    grade_level,
                    notes,
                    self._now(),
                    self._now(),
                ),
            )
            conn.commit()
            return cursor.lastrowid

    def get_person_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        normalized_name = (name or "").strip()
        if not normalized_name:
            return None

        with get_connection() as conn:
            row = conn.execute(
                """
                SELECT *
                FROM person_profiles
                WHERE LOWER(name) = LOWER(?)
                ORDER BY id ASC
                LIMIT 1
                """,
                (normalized_name,),
            ).fetchone()

        return dict(row) if row else None

    def get_person_by_role(self, role: str) -> Optional[Dict[str, Any]]:
        with get_connection() as conn:
            row = conn.execute(
                """
                SELECT *
                FROM person_profiles
                WHERE role = ?
                ORDER BY id ASC
                LIMIT 1
                """,
                (role,),
            ).fetchone()

        return dict(row) if row else None

    def update_person_profile(self, person_id: int, **fields) -> None:
        allowed_fields = {
            "name",
            "role",
            "birth_date",
            "school_name",
            "grade_level",
            "notes",
        }

        updates = []
        values = []

        for key, value in fields.items():
            if key in allowed_fields:
                updates.append(f"{key} = ?")
                values.append(value)

        if not updates:
            return

        updates.append("updated_at = ?")
        values.append(self._now())
        values.append(person_id)

        sql = f"""
        UPDATE person_profiles
        SET {", ".join(updates)}
        WHERE id = ?
        """

        with get_connection() as conn:
            conn.execute(sql, values)
            conn.commit()

    # =========================================================
    # EPISODIC MEMORY
    # =========================================================
    def add_episodic_memory(
        self,
        memory_text: str,
        person_id: Optional[int] = None,
        category: str = "general",
        importance: int = 1,
        tags: Optional[List[str]] = None,
        source: str = "conversation",
    ) -> int:
        memory_text = (memory_text or "").strip()
        if not memory_text:
            raise ValueError("memory_text boş olamaz")

        tags_json = json.dumps(tags or [], ensure_ascii=False)

        with get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO episodic_memories
                (person_id, memory_text, category, importance, tags_json, source, created_at, last_used_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    person_id,
                    memory_text,
                    category,
                    max(1, min(importance, 5)),
                    tags_json,
                    source,
                    self._now(),
                    None,
                ),
            )
            conn.commit()
            return cursor.lastrowid

    def search_memories(self, query: str, limit: int = 5) -> List[str]:
        """
        Basit lexical relevance v1.
        Daha sonra embedding / hybrid retrieval eklenebilir.
        """
        query_norm = self._normalize(query)
        if not query_norm:
            return []

        query_tokens = set(query_norm.split())
        if not query_tokens:
            return []

        with get_connection() as conn:
            rows = conn.execute(
                """
                SELECT id, memory_text, category, importance, tags_json, created_at, last_used_at
                FROM episodic_memories
                ORDER BY importance DESC, created_at DESC
                """
            ).fetchall()

        scored: List[tuple[int, int, str]] = []

        for row in rows:
            memory_text = row["memory_text"]
            memory_norm = self._normalize(memory_text)
            memory_tokens = set(memory_norm.split())

            overlap = len(query_tokens.intersection(memory_tokens))
            if overlap == 0:
                # tag eşleşmesi de deneyelim
                tags = self._safe_load_json(row["tags_json"])
                tag_score = 0
                for tag in tags:
                    tag_norm = self._normalize(str(tag))
                    if tag_norm and tag_norm in query_norm:
                        tag_score += 1

                if tag_score == 0:
                    continue
                score = tag_score + int(row["importance"] or 1)
            else:
                score = overlap * 3 + int(row["importance"] or 1)

            # Doğum günü gibi alakasız baskın memory'leri kısmen cezalandır
            lower_mem = memory_norm
            lower_query = query_norm
            repetitive_terms = {"dogum gunu", "30 mayis", "voleybol", "robot kulubu"}
            if any(term in lower_mem for term in repetitive_terms):
                if not any(term in lower_query for term in repetitive_terms):
                    score -= 2

            if score > 0:
                scored.append((score, row["id"], memory_text))

        scored.sort(key=lambda x: x[0], reverse=True)

        unique_texts = []
        seen = set()

        for score, memory_id, text in scored:
            key = self._normalize(text)
            if key in seen:
                continue
            seen.add(key)
            unique_texts.append(text)

            self._touch_memory(memory_id)

            if len(unique_texts) >= limit:
                break

        return unique_texts

    def _touch_memory(self, memory_id: int) -> None:
        with get_connection() as conn:
            conn.execute(
                """
                UPDATE episodic_memories
                SET last_used_at = ?
                WHERE id = ?
                """,
                (self._now(), memory_id),
            )
            conn.commit()

    # =========================================================
    # INTENT TEMPLATES
    # =========================================================
    def add_template(
        self,
        intent_name: str,
        template_text: str,
        tone: str = "neutral",
        lang: str = "tr",
        priority: int = 1,
        is_active: bool = True,
    ) -> int:
        with get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO intent_templates
                (intent_name, template_text, tone, lang, priority, is_active, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    intent_name,
                    template_text,
                    tone,
                    lang,
                    priority,
                    1 if is_active else 0,
                    self._now(),
                ),
            )
            conn.commit()
            return cursor.lastrowid

        import random
        from typing import Optional
        
        
        def get_template(self, intent_name: str, lang: str = "tr") -> Optional[str]:
            with get_connection() as conn:
                rows = conn.execute(
                    """
                    SELECT template_text
                    FROM intent_templates
                    WHERE intent_name = ?
                      AND lang = ?
                      AND is_active = 1
                    ORDER BY priority DESC, id ASC
                    """,
                    (intent_name, lang),
                ).fetchall()
        
            if not rows:
                return None
        
            templates = [r["template_text"] for r in rows]
        
            # son kullanılanı çıkar (varsa)
            if hasattr(self, "_last_template") and self._last_template in templates:
                templates.remove(self._last_template)
        
            choice = random.choice(templates)
            self._last_template = choice
        
            return choice

    # =========================================================
    # CONVERSATION LOGS
    # =========================================================
    def log_conversation(
        self,
        raw_text: Optional[str],
        normalized_text: Optional[str],
        intent: Optional[str],
        response_source: Optional[str],
        reply_text: Optional[str],
    ) -> int:
        with get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO conversation_logs
                (raw_text, normalized_text, intent, response_source, reply_text, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    raw_text,
                    normalized_text,
                    intent,
                    response_source,
                    reply_text,
                    self._now(),
                ),
            )
            conn.commit()
            return cursor.lastrowid

    # =========================================================
    # HELPERS
    # =========================================================
    def ensure_default_tanem_profile(self) -> int:
        """
        Tanem profilini yoksa oluşturur, varsa id döner.
        """
        existing = self.get_person_by_role("tanem")
        if existing:
            return existing["id"]

        return self.create_person_profile(
            name="Tanem",
            role="tanem",
            birth_date="2013-05-30",
            school_name=None,
            grade_level=None,
            notes="Ana kullanıcı profili"
        )

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
        t = re.sub(r"[^a-z0-9\s]", " ", t)
        t = re.sub(r"\s+", " ", t).strip()
        return t

    def _now(self) -> str:
        return datetime.utcnow().isoformat(timespec="seconds")

    def _safe_load_json(self, value: Optional[str]) -> List[Any]:
        if not value:
            return []
        try:
            loaded = json.loads(value)
            return loaded if isinstance(loaded, list) else []
        except Exception:
            return []
