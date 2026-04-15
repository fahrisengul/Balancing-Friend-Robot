import json
from memory.storage.db import get_connection


class MemoryManager:
    def __init__(self):
        self.init_db()

    def init_db(self):
        try:
            with get_connection() as conn:
                # debug tabloları
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
                conn.commit()
        except Exception as e:
            print(f"DB init error: {e}")

    # ===== LOG API (mevcutları koru) =====

    def log_retrieval_debug(self, **kwargs):
        try:
            with get_connection() as conn:
                conn.execute("""
                INSERT INTO retrieval_debug
                (session_id, intent, mode, query_text, query_variants_json,
                 selected_chunks_json, confidence, retrieval_source, context_chars)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    kwargs.get("session_id"),
                    kwargs.get("intent"),
                    kwargs.get("mode"),
                    kwargs.get("query_text"),
                    kwargs.get("query_variants_json"),
                    kwargs.get("selected_chunks_json"),
                    kwargs.get("confidence"),
                    kwargs.get("retrieval_source"),
                    kwargs.get("context_chars"),
                ))
                conn.commit()
        except Exception as e:
            print(f">>> [LOG RETRIEVAL ERROR] {e}")

    def log_streaming_debug(self, **kwargs):
        try:
            with get_connection() as conn:
                conn.execute("""
                INSERT INTO streaming_debug
                (session_id, intent, flush_count, first_flush_ms,
                 total_stream_ms, total_chunks, spoken_segments_json)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    kwargs.get("session_id"),
                    kwargs.get("intent"),
                    kwargs.get("flush_count"),
                    kwargs.get("first_flush_ms"),
                    kwargs.get("total_stream_ms"),
                    kwargs.get("total_chunks"),
                    kwargs.get("spoken_segments_json"),
                ))
                conn.commit()
        except Exception as e:
            print(f">>> [LOG STREAMING ERROR] {e}")

    def cleanup_logs(self):
        # stub
        return
    
    
    def rebuild_daily_metrics(self):
        # stub
        return
    
    
    def log_conversation(self, raw_text, normalized_text, intent, response_source, reply_text):
        try:
            with get_connection() as conn:
                conn.execute("""
                    INSERT INTO conversation_logs
                    (raw_text, normalized_text, intent, response_source, reply_text)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    raw_text,
                    normalized_text,
                    intent,
                    response_source,
                    reply_text,
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
                    (session_id, intent, response_source, model_name, latency_ms,
                     memory_context_used, status, error_text)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    session_id,
                    intent,
                    response_source,
                    model_name,
                    latency_ms,
                    1 if memory_context_used else 0,
                    status,
                    error_text,
                ))
                conn.commit()
        except Exception as e:
            print(f">>> [LOG TELEMETRY ERROR] {e}")
