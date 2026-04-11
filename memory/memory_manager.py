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

    conversations = [
        {
            "raw_text": r["raw_text"],
            "normalized_text": r["normalized_text"],
            "intent": r["intent"],
            "response_source": r["response_source"],
            "reply_text": r["reply_text"],
            "created_at": r["created_at"],
        }
        for r in conv_rows
    ]

    telemetry = [
        {
            "session_id": r["session_id"],
            "intent": r["intent"],
            "response_source": r["response_source"],
            "model_name": r["model_name"],
            "latency_ms": r["latency_ms"],
            "memory_context_used": r["memory_context_used"],
            "status": r["status"],
            "error_text": r["error_text"],
            "created_at": r["created_at"],
        }
        for r in telem_rows
    ]

    llm_calls = [
        {
            "session_id": r["session_id"],
            "intent": r["intent"],
            "model_name": r["model_name"],
            "prompt_chars": r["prompt_chars"],
            "response_chars": r["response_chars"],
            "latency_ms": r["latency_ms"],
            "status": r["status"],
            "error_text": r["error_text"],
            "created_at": r["created_at"],
        }
        for r in llm_rows
    ]

    return {
        "generated_at": self._now(),
        "session_id": None,
        "conversation_logs": conversations,
        "conversation_telemetry": telemetry,
        "llm_calls": llm_calls,
        "summary": {
            "conversation_count": len(conversations),
            "telemetry_count": len(telemetry),
            "llm_call_count": len(llm_calls),
        },
    }
