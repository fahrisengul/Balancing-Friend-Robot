import json
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from .db import get_connection, init_db

import random


class MemoryManager:
    """
    Profile + episodic memory + templates + runtime telemetry
    """

    def __init__(self):
        init_db()
        self._last_template: Optional[str] = None

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

            repetitive_terms = {"dogum gunu", "30 mayis", "voleybol", "robot kulubu"}
            if any(term in memory_norm for term in repetitive_terms):
                if not any(term in query_norm for term in repetitive_terms):
                    score -= 2

            if score > 0:
                scored.append((score, row["id"], memory_text))

        scored.sort(key=lambda x: x[0], reverse=True)

        unique_texts = []
        seen = set()

        for _, memory_id, text in scored:
            key = self._normalize(text)
            if key in seen:
                continue
            seen.add(key)
            unique_texts.append(text)
            self._touch_memory(memory_id)

            if len(unique_texts) >= limit:
                break

        return unique_texts

    def get_recent_memories(self, limit: int = 5) -> List[Dict[str, Any]]:
        with get_connection() as conn:
            rows = conn.execute(
                """
                SELECT id, memory_text, category, importance, created_at, last_used_at
                FROM episodic_memories
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()

        return [dict(r) for r in rows]

    def search_memories_by_keyword(self, keyword: str, limit: int = 5) -> List[Dict[str, Any]]:
        keyword = (keyword or "").strip()
        if not keyword:
            return []

        with get_connection() as conn:
            rows = conn.execute(
                """
                SELECT id, memory_text, category, importance, created_at
                FROM episodic_memories
                WHERE memory_text LIKE ?
                ORDER BY importance DESC, created_at DESC
                LIMIT ?
                """,
                (f"%{keyword}%", limit),
            ).fetchall()

        return [dict(r) for r in rows]

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

        if self._last_template in templates and len(templates) > 1:
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
        session_id: Optional[str] = None,
        model_name: Optional[str] = None,
        latency_ms: Optional[int] = None,
        memory_context_used: bool = False,
        status: str = "ok",
        error_text: Optional[str] = None,
    ) -> int:
        with get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO conversation_logs
                (session_id, raw_text, normalized_text, intent, response_source, reply_text,
                 model_name, latency_ms, memory_context_used, status, error_text, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    self._truncate(raw_text, 500),
                    self._truncate(normalized_text, 500),
                    intent,
                    response_source,
                    self._truncate(reply_text, 500),
                    model_name,
                    latency_ms,
                    1 if memory_context_used else 0,
                    status,
                    self._truncate(error_text, 500),
                    self._now(),
                ),
            )
            conn.commit()
            return cursor.lastrowid

    def log_llm_call(
        self,
        model_name: str,
        intent: Optional[str] = None,
        prompt_chars: int = 0,
        response_chars: int = 0,
        latency_ms: Optional[int] = None,
        session_id: Optional[str] = None,
        status: str = "ok",
        error_text: Optional[str] = None,
    ) -> int:
        with get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO llm_calls
                (session_id, intent, model_name, prompt_chars, response_chars, latency_ms,
                 status, error_text, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    intent,
                    model_name,
                    prompt_chars,
                    response_chars,
                    latency_ms,
                    status,
                    self._truncate(error_text, 500),
                    self._now(),
                ),
            )
            conn.commit()
            return cursor.lastrowid

    def log_system_event(self, event_type: str, detail_text: Optional[str] = None) -> int:
        with get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO system_events
                (event_type, detail_text, created_at)
                VALUES (?, ?, ?)
                """,
                (event_type, self._truncate(detail_text, 1000), self._now()),
            )
            conn.commit()
            return cursor.lastrowid

    # =========================================================
    # METRICS / EXPORT
    # =========================================================
    def rebuild_daily_metrics(self, metric_date: Optional[str] = None) -> None:
        """
        metric_date yoksa bugünün UTC tarihi kullanılır.
        """
        metric_date = metric_date or datetime.utcnow().strftime("%Y-%m-%d")
        day_start = f"{metric_date}T00:00:00"
        day_end_dt = datetime.strptime(metric_date, "%Y-%m-%d") + timedelta(days=1)
        day_end = day_end_dt.strftime("%Y-%m-%dT00:00:00")

        with get_connection() as conn:
            rows = conn.execute(
                """
                SELECT
                    COALESCE(intent, 'unknown') AS intent,
                    COALESCE(response_source, 'unknown') AS response_source,
                    COUNT(*) AS total_count,
                    AVG(COALESCE(latency_ms, 0)) AS avg_latency_ms,
                    AVG(LENGTH(COALESCE(reply_text, ''))) AS avg_reply_chars,
                    SUM(CASE WHEN response_source = 'llm' THEN 1 ELSE 0 END) AS llm_count,
                    SUM(CASE WHEN status = 'error' THEN 1 ELSE 0 END) AS error_count
                FROM conversation_logs
                WHERE created_at >= ? AND created_at < ?
                GROUP BY COALESCE(intent, 'unknown'), COALESCE(response_source, 'unknown')
                """,
                (day_start, day_end),
            ).fetchall()

            for row in rows:
                conn.execute(
                    """
                    INSERT INTO daily_metrics
                    (metric_date, intent, response_source, total_count, avg_latency_ms,
                     avg_reply_chars, llm_count, error_count, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(metric_date, intent, response_source)
                    DO UPDATE SET
                        total_count = excluded.total_count,
                        avg_latency_ms = excluded.avg_latency_ms,
                        avg_reply_chars = excluded.avg_reply_chars,
                        llm_count = excluded.llm_count,
                        error_count = excluded.error_count
                    """,
                    (
                        metric_date,
                        row["intent"],
                        row["response_source"],
                        row["total_count"],
                        row["avg_latency_ms"],
                        row["avg_reply_chars"],
                        row["llm_count"],
                        row["error_count"],
                        self._now(),
                    ),
                )

            conn.commit()

    def export_review_bundle(
        self,
        session_id: Optional[str] = None,
        limit: int = 200,
    ) -> Dict[str, Any]:
        """
        ChatGPT'ye yüklemek için küçük ama anlamlı paket.
        """
        with get_connection() as conn:
            params: List[Any]
            if session_id:
                rows = conn.execute(
                    """
                    SELECT created_at, raw_text, intent, response_source, reply_text,
                           model_name, latency_ms, memory_context_used, status, error_text
                    FROM conversation_logs
                    WHERE session_id = ?
                    ORDER BY id DESC
                    LIMIT ?
                    """,
                    (session_id, limit),
                ).fetchall()

                llm_rows = conn.execute(
                    """
                    SELECT created_at, intent, model_name, prompt_chars, response_chars,
                           latency_ms, status, error_text
                    FROM llm_calls
                    WHERE session_id = ?
                    ORDER BY id DESC
                    LIMIT ?
                    """,
                    (session_id, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT created_at, raw_text, intent, response_source, reply_text,
                           model_name, latency_ms, memory_context_used, status, error_text
                    FROM conversation_logs
                    ORDER BY id DESC
                    LIMIT ?
                    """,
                    (limit,),
                ).fetchall()

                llm_rows = conn.execute(
                    """
                    SELECT created_at, intent, model_name, prompt_chars, response_chars,
                           latency_ms, status, error_text
                    FROM llm_calls
                    ORDER BY id DESC
                    LIMIT ?
                    """,
                    (limit,),
                ).fetchall()

        conversations = [dict(r) for r in rows]
        llm_calls = [dict(r) for r in llm_rows]

        by_source: Dict[str, int] = {}
        by_intent: Dict[str, int] = {}
        errors = 0

        for row in conversations:
            src = row.get("response_source") or "unknown"
            by_source[src] = by_source.get(src, 0) + 1

            intent = row.get("intent") or "unknown"
            by_intent[intent] = by_intent.get(intent, 0) + 1

            if row.get("status") == "error":
                errors += 1

        return {
            "generated_at": self._now(),
            "session_id": session_id,
            "summary": {
                "conversation_count": len(conversations),
                "llm_call_count": len(llm_calls),
                "error_count": errors,
                "by_source": by_source,
                "by_intent": by_intent,
            },
            "conversation_logs": conversations,
            "llm_calls": llm_calls,
        }

    # =========================================================
    # CLEANUP / RETENTION
    # =========================================================
    def cleanup_logs(
        self,
        conversation_days: int = 30,
        llm_days: int = 90,
        system_event_days: int = 60,
        run_vacuum: bool = True,
    ) -> Dict[str, int]:
        conv_cutoff = self._days_ago(conversation_days)
        llm_cutoff = self._days_ago(llm_days)
        sys_cutoff = self._days_ago(system_event_days)

        with get_connection() as conn:
            conv_deleted = conn.execute(
                "DELETE FROM conversation_logs WHERE created_at < ?",
                (conv_cutoff,),
            ).rowcount

            llm_deleted = conn.execute(
                "DELETE FROM llm_calls WHERE created_at < ?",
                (llm_cutoff,),
            ).rowcount

            sys_deleted = conn.execute(
                "DELETE FROM system_events WHERE created_at < ?",
                (sys_cutoff,),
            ).rowcount

            conn.commit()

            if run_vacuum:
                conn.execute("VACUUM")

        detail = (
            f"cleanup completed | conversation_logs={conv_deleted}, "
            f"llm_calls={llm_deleted}, system_events={sys_deleted}"
        )
        self.log_system_event("cleanup", detail)

        return {
            "conversation_logs_deleted": conv_deleted,
            "llm_calls_deleted": llm_deleted,
            "system_events_deleted": sys_deleted,
        }

    # =========================================================
    # HELPERS
    # =========================================================
    def ensure_default_tanem_profile(self) -> int:
        existing = self.get_person_by_role("tanem")
        if existing:
            return existing["id"]

        return self.create_person_profile(
            name="Tanem",
            role="tanem",
            birth_date="2013-05-30",
            school_name=None,
            grade_level=None,
            notes="Ana kullanıcı profili",
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

    def _days_ago(self, days: int) -> str:
        return (datetime.utcnow() - timedelta(days=days)).isoformat(timespec="seconds")

    def _truncate(self, value: Optional[str], max_len: int) -> Optional[str]:
        if value is None:
            return None
        return value[:max_len]

    def _safe_load_json(self, value: Optional[str]) -> List[Any]:
        if not value:
            return []
        try:
            loaded = json.loads(value)
            return loaded if isinstance(loaded, list) else []
        except Exception:
            return []
