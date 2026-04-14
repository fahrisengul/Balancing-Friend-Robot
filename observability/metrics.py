import json
import time


def log_streaming(memory, intent, started_at, spoken_segments, flush_count, first_flush_ms):
    total_stream_ms = int((time.perf_counter() - started_at) * 1000)
    try:
        memory.log_streaming_debug(
            session_id=None,
            intent=intent,
            flush_count=flush_count,
            first_flush_ms=first_flush_ms,
            total_stream_ms=total_stream_ms,
            total_chunks=len(spoken_segments),
            spoken_segments_json=json.dumps(spoken_segments[:20], ensure_ascii=False),
        )
    except Exception as e:
        print(f">>> [METRICS STREAMING ERROR] {e}")


def log_retrieval(memory, **kwargs):
    try:
        memory.log_retrieval_debug(**kwargs)
    except Exception as e:
        print(f">>> [METRICS RETRIEVAL ERROR] {e}")


def log_llm(memory, **kwargs):
    try:
        memory.log_llm_call(**kwargs)
    except Exception as e:
        print(f">>> [METRICS LLM ERROR] {e}")


def log_telemetry(memory, **kwargs):
    try:
        memory.log_conversation_telemetry(**kwargs)
    except Exception as e:
        print(f">>> [METRICS TELEMETRY ERROR] {e}")
