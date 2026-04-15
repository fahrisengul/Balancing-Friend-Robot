import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from memory.storage.db import get_connection


class MemoryManager:
    def __init__(self):
        self.init_db()

    # =========================================================
    # DB INIT
    # =========================================================
    def init_db(self):
        try:
            with get_connection() as conn:
                conn.execute("""
                CREATE TABLE IF NOT EXISTS retrieval_debug (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT,
                    intent TEXT,
                    mode TEXT,
                    query_text TEXT,
                    query_variants_json TEXT,
                    selected_chunks_json TEXT,
                    confidence REAL,
                    retrieval_source TEXT,
                    context_chars INTEGER,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
                """)

                conn.execute("""
                CREATE TABLE IF NOT EXISTS streaming_debug (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT,
                    intent TEXT,
                    flush_count INTEGER,
                    first_flush_ms INTEGER,
                    total_stream_ms INTEGER,
                    total_chunks INTEGER,
                    spoken_segments_json TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
                """)

                conn.execute("""
                CREATE TABLE IF NOT EXISTS system_params (
                    param_key TEXT PRIMARY KEY,
                    param_value TEXT,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
                """)

                conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_conversation_logs_created_at
                ON conversation_logs(created_at DESC)
                """)

                conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_llm_calls_created_at
                ON llm_calls(created_at DESC)
                """)

                conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_retrieval_debug_created_at
                ON retrieval_debug(created_at DESC)
                """)

                conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_streaming_debug_created_at
                ON streaming_debug(created_at DESC)
                """)

                conn.commit()
        except Exception as e:
            print(f"DB init error: {e}")

    # =========================================================
    # COMPATIBILITY / MAINTENANCE
    # =========================================================
    def cleanup_logs(self):
        return

    def rebuild_daily_metrics(self):
        return

    # =========================================================
    # FAST / TEMPLATE HELPERS
    # =========================================================
    def get_template(self, intent_name: str) -> Optional[str]:
        try:
            with get_connection() as conn:
                cur = conn.cursor()
                cur.execute("""
                    SELECT template_text
                    FROM intent_templates
                    WHERE intent_name = ? AND is_active = 1
                    ORDER BY id DESC
                    LIMIT 1
                """, (intent_name,))
                row = cur.fetchone()
                return row[0] if row else None
        except Exception as e:
            print(f">>> [GET TEMPLATE ERROR] {e}")
            return None

    def search_fast_answer(self, text: str, intent: Optional[str] = None) -> Optional[str]:
        try:
            if intent:
                template = self.get_template(intent)
                if template:
                    return template

            normalized = (text or "").strip().lower()

            with get_connection() as conn:
                cur = conn.cursor()
                cur.execute("""
                    SELECT answer_text
                    FROM fast_answers
                    WHERE is_active = 1
                    AND (
                        normalized_question = ?
                        OR question_text = ?
                    )
                    ORDER BY id DESC
                    LIMIT 1
                """, (normalized, text))
                row = cur.fetchone()
                return row[0] if row else None
        except Exception:
            return None

    # =========================================================
    # LOG METHODS
    # =========================================================
    def log_retrieval_debug(
        self,
        session_id=None,
        intent=None,
        mode=None,
        query_text=None,
        query_variants_json=None,
        selected_chunks_json=None,
        confidence=None,
        retrieval_source=None,
        context_chars=None,
    ):
        try:
            with get_connection() as conn:
                conn.execute("""
                    INSERT INTO retrieval_debug
                    (session_id, intent, mode, query_text, query_variants_json,
                     selected_chunks_json, confidence, retrieval_source, context_chars)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    session_id,
                    intent,
                    mode,
                    query_text,
                    query_variants_json,
                    selected_chunks_json,
                    confidence,
                    retrieval_source,
                    context_chars,
                ))
                conn.commit()
        except Exception as e:
            print(f">>> [LOG RETRIEVAL ERROR] {e}")

    def log_streaming_debug(
        self,
        session_id=None,
        intent=None,
        flush_count=None,
        first_flush_ms=None,
        total_stream_ms=None,
        total_chunks=None,
        spoken_segments_json=None,
    ):
        try:
            with get_connection() as conn:
                conn.execute("""
                    INSERT INTO streaming_debug
                    (session_id, intent, flush_count, first_flush_ms,
                     total_stream_ms, total_chunks, spoken_segments_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    session_id,
                    intent,
                    flush_count,
                    first_flush_ms,
                    total_stream_ms,
                    total_chunks,
                    spoken_segments_json,
                ))
                conn.commit()
        except Exception as e:
            print(f">>> [LOG STREAMING ERROR] {e}")

    def log_conversation(
        self,
        raw_text,
        normalized_text,
        intent,
        response_source,
        reply_text,
        session_id=None,
        model_name=None,
        latency_ms=None,
        memory_context_used=False,
        status="ok",
        error_text=None,
    ):
        try:
            with get_connection() as conn:
                conn.execute("""
                    INSERT INTO conversation_logs
                    (session_id, raw_text, normalized_text, intent, response_source,
                     reply_text, model_name, latency_ms, memory_context_used, status, error_text)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    session_id,
                    raw_text,
                    normalized_text,
                    intent,
                    response_source,
                    reply_text,
                    model_name,
                    latency_ms,
                    1 if memory_context_used else 0,
                    status,
                    error_text,
                ))
                conn.commit()
        except Exception as e:
            print(f">>> [LOG CONVERSATION ERROR] {e}")

    def log_conversation_telemetry(
        self,
        session_id=None,
        intent=None,
        response_source=None,
        model_name=None,
        latency_ms=None,
        memory_context_used=False,
        status="ok",
        error_text=None,
    ):
        try:
            with get_connection() as conn:
                conn.execute("""
                    INSERT INTO conversation_logs
                    (session_id, raw_text, normalized_text, intent, response_source,
                     reply_text, model_name, latency_ms, memory_context_used, status, error_text)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    session_id,
                    None,
                    None,
                    intent,
                    response_source,
                    None,
                    model_name,
                    latency_ms,
                    1 if memory_context_used else 0,
                    status,
                    error_text,
                ))
                conn.commit()
        except Exception as e:
            print(f">>> [LOG TELEMETRY ERROR] {e}")

    def log_llm_call(
        self,
        session_id=None,
        intent=None,
        model_name=None,
        prompt_chars=None,
        response_chars=None,
        latency_ms=None,
        status="ok",
        error_text=None,
    ):
        try:
            with get_connection() as conn:
                conn.execute("""
                    INSERT INTO llm_calls
                    (session_id, intent, model_name, prompt_chars, response_chars,
                     latency_ms, status, error_text)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    session_id,
                    intent,
                    model_name,
                    prompt_chars,
                    response_chars,
                    latency_ms,
                    status,
                    error_text,
                ))
                conn.commit()
        except Exception as e:
            print(f">>> [LOG LLM ERROR] {e}")

    # =========================================================
    # EXPORT / REVIEW
    # =========================================================
    def export_review_bundle(self, limit: int = 200) -> Dict[str, Any]:
        return {
            "generated_at": self._now_iso(),
            "conversation_logs": self._fetch_rows("""
                SELECT raw_text, normalized_text, intent, response_source, reply_text, created_at
                FROM conversation_logs
                ORDER BY id DESC
                LIMIT ?
            """, (limit,)),
            "llm_calls": self._fetch_rows("""
                SELECT session_id, intent, model_name, prompt_chars, response_chars,
                       latency_ms, status, error_text, created_at
                FROM llm_calls
                ORDER BY id DESC
                LIMIT ?
            """, (limit,)),
            "retrieval_debug": self._fetch_rows("""
                SELECT session_id, intent, mode, query_text, query_variants_json,
                       selected_chunks_json, confidence, retrieval_source, context_chars, created_at
                FROM retrieval_debug
                ORDER BY id DESC
                LIMIT ?
            """, (limit,)),
            "streaming_debug": self._fetch_rows("""
                SELECT session_id, intent, flush_count, first_flush_ms,
                       total_stream_ms, total_chunks, spoken_segments_json, created_at
                FROM streaming_debug
                ORDER BY id DESC
                LIMIT ?
            """, (limit,)),
        }

    # =========================================================
    # INTERNAL HELPERS
    # =========================================================
    def _fetch_rows(self, sql: str, params: tuple = ()) -> List[Dict[str, Any]]:
        try:
            with get_connection() as conn:
                conn.row_factory = self._dict_factory
                cur = conn.cursor()
                cur.execute(sql, params)
                rows = cur.fetchall()
                return rows if rows else []
        except Exception as e:
            print(f">>> [EXPORT ERROR] {e}")
            return []

    @staticmethod
    def _dict_factory(cursor, row):
        return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}

    @staticmethod
    def _now_iso() -> str:
        return datetime.now().isoformat()
