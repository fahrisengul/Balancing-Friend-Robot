import sqlite3
from datetime import datetime, timedelta

DB_PATH = "memory/poodle.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


class MemoryManager:
    def _now(self):
        return datetime.utcnow().isoformat()

    def _tr(self, txt, max_len=500):
        if txt is None:
            return None
        return str(txt)[:max_len]

    # =========================================================
    # PERSON
    # =========================================================
    def get_person_by_role(self, role):
        with get_connection() as conn:
            row = conn.execute(
                """
                SELECT *
                FROM person_profiles
                WHERE role = ?
                LIMIT 1
                """,
                (role,),
            ).fetchone()
        return dict(row) if row else None

    def upsert_person_profile(self, role, name):
        existing = self.get_person_by_role(role)

        with get_connection() as conn:
            if existing:
                conn.execute(
                    """
                    UPDATE person_profiles
                    SET name = ?
                    WHERE role = ?
                    """,
                    (name, role),
                )
            else:
                conn.execute(
                    """
                    INSERT INTO person_profiles (name, role, birth_date, created_at)
                    VALUES (?, ?, ?, ?)
                    """,
                    (name, role, None, self._now()),
                )
            conn.commit()

    # =========================================================
    # EPISODIC MEMORY
    # =========================================================
    def add_episodic_memory(
        self,
        content,
        timestamp=None,
        category="general",
        importance=1,
        person_id=None,
    ):
        ts = timestamp or self._now()

        with get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO episodic_memories
                (person_id, memory_text, category, importance, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (person_id, content, category, importance, ts),
            )
            conn.commit()
            memory_id = cursor.lastrowid

        print(f">>> [MEMORY] memory_id={memory_id} kaydedildi")
        return memory_id

    def get_memory_by_id(self, memory_id):
        with get_connection() as conn:
            row = conn.execute(
                """
                SELECT memory_text
                FROM episodic_memories
                WHERE id = ?
                """,
                (memory_id,),
            ).fetchone()
        return row["memory_text"] if row else None

    def search_memories(self, text, limit=3):
        with get_connection() as conn:
            rows = conn.execute(
                """
                SELECT memory_text
                FROM episodic_memories
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [r["memory_text"] for r in rows]

    # =========================================================
    # INTENT / TEMPLATE
    # =========================================================
    def get_template(self, intent_name=None):
        if not intent_name:
            return None

        with get_connection() as conn:
            row = conn.execute(
                """
                SELECT template_text
                FROM intent_templates
                WHERE intent_name = ?
                  AND is_active = 1
                ORDER BY priority DESC, id ASC
                LIMIT 1
                """,
                (intent_name,),
            ).fetchone()

        return row["template_text"] if row else None

    # =========================================================
    # FAST ANSWERS
    # =========================================================
    def search_fast_answer(self, text, intent=None):
        t = (text or "").strip().lower()

        with get_connection() as conn:
            rows = conn.execute(
                """
                SELECT intent, pattern, answer, priority
                FROM fast_answers
                ORDER BY priority DESC, id ASC
                """
            ).fetchall()

        best = None
        for row in rows:
            pattern = (row["pattern"] or "").strip().lower()
            row_intent = row["intent"]

            if intent and row_intent and row_intent == intent:
                if pattern and pattern in t:
                    best = row["answer"]
                    break

            if pattern and pattern in t:
                best = row["answer"]
                break

        return best

    # =========================================================
    # EDUCATION DATA
    # =========================================================
    def get_education_snippets_by_topic(self, topic_name, limit=3):
        with get_connection() as conn:
            rows = conn.execute(
                """
                SELECT content, type
                FROM education_snippets
                WHERE lower(topic_name) = lower(?)
                ORDER BY id ASC
                LIMIT ?
                """,
                (topic_name, limit),
            ).fetchall()

        return [dict(r) for r in rows]

    def search_education_snippets(self, text, limit=3):
        t = (text or "").strip().lower()

        with get_connection() as conn:
            rows = conn.execute(
                """
                SELECT topic_name, content, type
                FROM education_snippets
                ORDER BY id ASC
                """
            ).fetchall()

        hits = []
        for row in rows:
            topic = (row["topic_name"] or "").lower()
            content = (row["content"] or "").lower()

            if topic in t or any(token in content for token in t.split() if len(token) > 2):
                hits.append(dict(row))
                if len(hits) >= limit:
                    break

        return hits

    # =========================================================
    # LOGGING
    # =========================================================
    def log_conversation(self, **kwargs):
        with get_connection() as conn:
            conn.execute(
                """
                INSERT INTO conversation_logs
                (raw_text, normalized_text, intent, response_source, reply_text, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    self._tr(kwargs.get("raw_text")),
                    self._tr(kwargs.get("normalized_text")),
                    kwargs.get("intent"),
                    kwargs.get("response_source"),
                    self._tr(kwargs.get("reply_text")),
                    self._now(),
                ),
            )
            conn.commit()

    def log_conversation_telemetry(self, **kwargs):
        with get_connection() as conn:
            conn.execute(
                """
                INSERT INTO conversation_telemetry
                (session_id, intent, response_source, model_name,
                 latency_ms, memory_context_used, status, error_text, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    kwargs.get("session_id"),
                    kwargs.get("intent"),
                    kwargs.get("response_source"),
                    kwargs.get("model_name"),
                    kwargs.get("latency_ms"),
                    1 if kwargs.get("memory_context_used") else 0,
                    kwargs.get("status", "ok"),
                    self._tr(kwargs.get("error_text")),
                    self._now(),
                ),
            )
            conn.commit()

    def log_llm_call(self, **kwargs):
        with get_connection() as conn:
            conn.execute(
                """
                INSERT INTO llm_calls
                (session_id, intent, model_name,
                 prompt_chars, response_chars,
                 latency_ms, status, error_text, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    kwargs.get("session_id"),
                    kwargs.get("intent"),
                    kwargs.get("model_name"),
                    kwargs.get("prompt_chars", 0),
                    kwargs.get("response_chars", 0),
                    kwargs.get("latency_ms"),
                    kwargs.get("status", "ok"),
                    self._tr(kwargs.get("error_text")),
                    self._now(),
                ),
            )
            conn.commit()

    def cleanup_logs(self):
        now = datetime.utcnow()

        telemetry_cut = (now - timedelta(days=30)).isoformat()
        llm_cut = (now - timedelta(days=90)).isoformat()
        sys_cut = (now - timedelta(days=60)).isoformat()

        with get_connection() as conn:
            conn.execute("DELETE FROM conversation_telemetry WHERE created_at < ?", (telemetry_cut,))
            conn.execute("DELETE FROM llm_calls WHERE created_at < ?", (llm_cut,))
            conn.execute("DELETE FROM system_events WHERE created_at < ?", (sys_cut,))
            conn.commit()

    def rebuild_daily_metrics(self):
        today = datetime.utcnow().strftime("%Y-%m-%d")

        with get_connection() as conn:
            rows = conn.execute(
                """
                SELECT
                    intent,
                    response_source,
                    COUNT(*) AS total_count,
                    AVG(latency_ms) AS avg_latency_ms,
                    SUM(CASE WHEN response_source='llm' THEN 1 ELSE 0 END) AS llm_count,
                    SUM(CASE WHEN status='error' THEN 1 ELSE 0 END) AS error_count
                FROM conversation_telemetry
                WHERE date(created_at)=?
                GROUP BY intent, response_source
                """,
                (today,),
            ).fetchall()

            for r in rows:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO daily_metrics
                    (metric_date, intent, response_source,
                     total_count, avg_latency_ms, llm_count, error_count)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        today,
                        r["intent"],
                        r["response_source"],
                        r["total_count"],
                        r["avg_latency_ms"],
                        r["llm_count"],
                        r["error_count"],
                    ),
                )

    def export_review_bundle(self, limit=200):
            with get_connection() as conn:
                conv_rows = conn.execute(
                    """
                    SELECT raw_text, normalized_text, intent, response_source, reply_text, created_at
                    FROM conversation_logs
                    ORDER BY id DESC
                    LIMIT ?
                    """,
                    (limit,),
                ).fetchall()
    
                telem_rows = conn.execute(
                    """
                    SELECT session_id, intent, response_source, model_name,
                           latency_ms, memory_context_used, status, error_text, created_at
                    FROM conversation_telemetry
                    ORDER BY id DESC
                    LIMIT ?
                    """,
                    (limit,),
                ).fetchall()
    
                llm_rows = conn.execute(
                    """
                    SELECT session_id, intent, model_name,
                           prompt_chars, response_chars,
                           latency_ms, status, error_text, created_at
                    FROM llm_calls
                    ORDER BY id DESC
                    LIMIT ?
                    """,
                    (limit,),
                ).fetchall()
    
            conversations = [dict(r) for r in conv_rows]
            telemetry = [dict(r) for r in telem_rows]
            llm_calls = [dict(r) for r in llm_rows]
    
            return {
                "generated_at": self._now(),
                "conversation_logs": conversations,
                "conversation_telemetry": telemetry,
                "llm_calls": llm_calls,
                "summary": {
                    "conversation_count": len(conversations),
                    "telemetry_count": len(telemetry),
                    "llm_call_count": len(llm_calls),
                },
            }
    conn.commit()
