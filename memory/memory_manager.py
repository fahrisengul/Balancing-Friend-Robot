import random
from typing import Optional
from .db import get_connection


class MemoryManager:

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

    def get_person_by_role(self, role: str):
        with get_connection() as conn:
            row = conn.execute(
                """
                SELECT name, data
                FROM persons
                WHERE role = ?
                LIMIT 1
                """,
                (role,),
            ).fetchone()

        if not row:
            return None

        return {
            "name": row["name"],
            "data": row["data"]
        }

    def add_template(self, intent_name: str, template_text: str, lang: str = "tr"):
        with get_connection() as conn:
            conn.execute(
                """
                INSERT INTO intent_templates (intent_name, template_text, lang, is_active)
                VALUES (?, ?, ?, 1)
                """,
                (intent_name, template_text, lang),
            )
            conn.commit()
