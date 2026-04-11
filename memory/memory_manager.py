import sqlite3
from datetime import datetime, timedelta

DB_PATH = "memory/poodle.db"


def get_connection():
    return sqlite3.connect(DB_PATH)


class MemoryManager:
    # =========================================================
    # BASIC HELPERS
    # =========================================================
    def _now(self):
        return datetime.utcnow().isoformat()

    def _tr(self, txt, max_len=500):
        if txt is None:
            return None
        return str(txt)[:max_len]

    # =========================================================
    # OLD CONVERSATION LOG
    # conversation_logs -> eski sade yapı
    # =========================================================
    def log_conversation(self, **kwargs):
        """
        conversation_logs tablosuna yazar.
        Beklenen kolonlar:
            id
            raw_text
            normalized_text
            intent
            response_source
            reply_text
            created_at
        """
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

    # =========================================================
    # NEW TELEMETRY LOG
    # conversation_telemetry -> yeni telemetry yapısı
    # =========================================================
    def log_conversation_telemetry(self, **kwargs):
        """
        conversation_telemetry tablosuna yazar.
        Beklenen kolonlar:
            id
            session_id
            intent
            response_source
            model_name
            latency_ms
            memory_context_used
            status
            error_text
            created_at
        """
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

    # =========================================================
    # LLM TELEMETRY
    # =========================================================
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

    # =========================================================
    # SYSTEM EVENTS
    # =========================================================
    def log_system_event(self, event_type, detail_text=None):
        with get_connection() as conn:
            conn.execute(
                """
                INSERT INTO system_events
                (event_type, detail_text, created_at)
                VALUES (?, ?, ?)
                """,
                (
                    event_type,
                    self._tr(detail_text, max_len=1000),
                    self._now(),
                ),
            )
            conn.commit()

    # =========================================================
    # CLEANUP
    # conversation_logs -> ürün geçmişi gibi de kullanılabilir, silmiyoruz
    # conversation_telemetry -> 30 gün
    # llm_calls -> 90 gün
    # system_events -> 60 gün
    # =========================================================
    def cleanup_logs(self):
        now = datetime.utcnow()

        telemetry_cut = (now - timedelta(days=30)).isoformat()
        llm_cut = (now - timedelta(days=90)).isoformat()
        sys_cut = (now - timedelta(days=60)).isoformat()

        with get_connection() as conn:
            conn.execute(
                "DELETE FROM conversation_telemetry WHERE created_at < ?",
                (telemetry_cut,),
            )
            conn.execute(
                "DELETE FROM llm_calls WHERE created_at < ?",
                (llm_cut,),
            )
            conn.execute(
                "DELETE FROM system_events WHERE created_at < ?",
                (sys_cut,),
            )
            conn.commit()

        self.log_system_event(
            "cleanup",
            "conversation_telemetry=30d, llm_calls=90d, system_events=60d retention uygulandı",
        )

    # =========================================================
    # DAILY METRICS
    # daily_metrics -> conversation_telemetry üzerinden rebuild edilir
    # =========================================================
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
                        r[0],
                        r[1],
                        r[2],
                        r[3],
                        r[4],
                        r[5],
                    ),
                )

            conn.commit()

    # =========================================================
    # REVIEW EXPORT
    # =========================================================
    def export_review_bundle(self, session_id=None, limit=200):
        with get_connection() as conn:
            if session_id:
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
                    WHERE session_id = ?
                    ORDER BY id DESC
                    LIMIT ?
                    """,
                    (session_id, limit),
                ).fetchall()

                llm_rows = conn.execute(
                    """
                    SELECT session_id, intent, model_name, prompt_chars, response_chars,
                           latency_ms, status, error_text, created_at
                    FROM llm_calls
                    WHERE session_id = ?
                    ORDER BY id DESC
                    LIMIT ?
                    """,
                    (session_id, limit),
                ).fetchall()
            else:
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
                    SELECT session_id, intent, model_name, prompt_chars, response_chars,
                           latency_ms, status, error_text, created_at
                    FROM llm_calls
                    ORDER BY id DESC
                    LIMIT ?
                    """,
                    (limit,),
                ).fetchall()

        conversations = [
            {
                "raw_text": r[0],
                "normalized_text": r[1],
                "intent": r[2],
                "response_source": r[3],
                "reply_text": r[4],
                "created_at": r[5],
            }
            for r in conv_rows
        ]

        telemetry = [
            {
                "session_id": r[0],
                "intent": r[1],
                "response_source": r[2],
                "model_name": r[3],
                "latency_ms": r[4],
                "memory_context_used": r[5],
                "status": r[6],
                "error_text": r[7],
                "created_at": r[8],
            }
            for r in telem_rows
        ]

        llm_calls = [
            {
                "session_id": r[0],
                "intent": r[1],
                "model_name": r[2],
                "prompt_chars": r[3],
                "response_chars": r[4],
                "latency_ms": r[5],
                "status": r[6],
                "error_text": r[7],
                "created_at": r[8],
            }
            for r in llm_rows
        ]

        return {
            "generated_at": self._now(),
            "session_id": session_id,
            "conversation_logs": conversations,
            "conversation_telemetry": telemetry,
            "llm_calls": llm_calls,
            "summary": {
                "conversation_count": len(conversations),
                "telemetry_count": len(telemetry),
                "llm_call_count": len(llm_calls),
            },
        }
