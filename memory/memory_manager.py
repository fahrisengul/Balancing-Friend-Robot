import random
import json
from typing import Optional
from .db import get_connection


class MemoryManager:

    # -------------------------------------------------
    # TEMPLATE GET
    # -------------------------------------------------
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
        return random.choice(templates)

    # -------------------------------------------------
    # PERSON GET
    # -------------------------------------------------
    def get_person_by_role(self, role: str):
        with get_connection() as conn:
            row = conn.execute(
                """
                SELECT id, name, role, birth_date, school_name, grade_level, notes
                FROM person_profiles
                WHERE role = ?
                LIMIT 1
                """,
                (role,),
            ).fetchone()

        if not row:
            return None

        return dict(row)

    # -------------------------------------------------
    # PERSON CREATE
    # -------------------------------------------------
    def create_person_profile(
        self,
        name,
        role,
        birth_date=None,
        school_name=None,
        grade_level=None,
        notes=None,
    ):
        with get_connection() as conn:
            conn.execute(
                """
                INSERT INTO person_profiles
                (name, role, birth_date, school_name, grade_level, notes)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (name, role, birth_date, school_name, grade_level, notes),
            )
            conn.commit()

    # -------------------------------------------------
    # MEMORY ADD
    # -------------------------------------------------
    def add_episodic_memory(
        self,
        memory_text,
        person_id=None,
        category="general",
        importance=1,
        tags=None,
    ):
        tags_json = json.dumps(tags or [])

        with get_connection() as conn:
            conn.execute(
                """
                INSERT INTO episodic_memories
                (person_id, memory_text, category, importance, tags_json)
                VALUES (?, ?, ?, ?, ?)
                """,
                (person_id, memory_text, category, importance, tags_json),
            )
            conn.commit()

    # -------------------------------------------------
    # TEMPLATE ADD
    # -------------------------------------------------
    def add_template(
        self,
        intent_name: str,
        template_text: str,
        tone: str = "neutral",
        lang: str = "tr",
        priority: int = 0,
        is_active: int = 1,
    ):
        with get_connection() as conn:
            conn.execute(
                """
                INSERT INTO intent_templates
                (intent_name, template_text, tone, lang, priority, is_active)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (intent_name, template_text, tone, lang, priority, is_active),
            )
            conn.commit()
