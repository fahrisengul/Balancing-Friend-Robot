import sqlite3
from datetime import datetime, timedelta

DB_PATH = "memory/poodle.db"


def get_connection():
    return sqlite3.connect(DB_PATH)


class MemoryManager:

    def log_conversation(self, **kwargs):
        with get_connection() as conn:
            conn.execute("""
                INSERT INTO conversation_logs
                (session_id, raw_text, normalized_text, intent,
                 response_source, reply_text, model_name,
                 latency_ms, memory_context_used,
                 status, error_text, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                kwargs.get("session_id"),
                self._tr(kwargs.get("raw_text")),
                self._tr(kwargs.get("normalized_text")),
                kwargs.get("intent"),
                kwargs.get("response_source"),
                self._tr(kwargs.get("reply_text")),
                kwargs.get("model_name"),
                kwargs.get("latency_ms"),
                1 if kwargs.get("memory_context_used") else 0,
                kwargs.get("status", "ok"),
                self._tr(kwargs.get("error_text")),
                self._now()
            ))
            conn.commit()

    def log_llm_call(self, **kwargs):
        with get_connection() as conn:
            conn.execute("""
                INSERT INTO llm_calls
                (session_id, intent, model_name,
                 prompt_chars, response_chars,
                 latency_ms, status, error_text, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                kwargs.get("session_id"),
                kwargs.get("intent"),
                kwargs.get("model_name"),
                kwargs.get("prompt_chars", 0),
                kwargs.get("response_chars", 0),
                kwargs.get("latency_ms"),
                kwargs.get("status", "ok"),
                self._tr(kwargs.get("error_text")),
                self._now()
            ))
            conn.commit()

    def cleanup_logs(self):
        now = datetime.utcnow()

        conv_cut = (now - timedelta(days=30)).isoformat()
        llm_cut = (now - timedelta(days=90)).isoformat()
        sys_cut = (now - timedelta(days=60)).isoformat()

        with get_connection() as conn:
            conn.execute("DELETE FROM conversation_logs WHERE created_at < ?", (conv_cut,))
            conn.execute("DELETE FROM llm_calls WHERE created_at < ?", (llm_cut,))
            conn.execute("DELETE FROM system_events WHERE created_at < ?", (sys_cut,))
            conn.commit()

    def rebuild_daily_metrics(self):
        today = datetime.utcnow().strftime("%Y-%m-%d")

        with get_connection() as conn:
            rows = conn.execute("""
                SELECT intent, response_source,
                       COUNT(*),
                       AVG(latency_ms),
                       SUM(CASE WHEN response_source='llm' THEN 1 ELSE 0 END),
                       SUM(CASE WHEN status='error' THEN 1 ELSE 0 END)
                FROM conversation_logs
                WHERE date(created_at)=?
                GROUP BY intent, response_source
            """, (today,)).fetchall()

            for r in rows:
                conn.execute("""
                    INSERT OR REPLACE INTO daily_metrics
                    (metric_date, intent, response_source,
                     total_count, avg_latency_ms, llm_count, error_count)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (today, r[0], r[1], r[2], r[3], r[4], r[5]))

            conn.commit()

    def _now(self):
        return datetime.utcnow().isoformat()

    def _tr(self, txt, max_len=500):
        if not txt:
            return txt
        return txt[:max_len]
