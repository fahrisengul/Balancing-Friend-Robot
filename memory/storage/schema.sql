PRAGMA foreign_keys = ON;

-- ===============================
-- PERSON
-- ===============================
CREATE TABLE IF NOT EXISTS person_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    role TEXT,
    birth_date TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- ===============================
-- MEMORY
-- ===============================
CREATE TABLE IF NOT EXISTS episodic_memories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    person_id INTEGER,
    memory_text TEXT,
    category TEXT,
    importance INTEGER DEFAULT 1,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- ===============================
-- TEMPLATES
-- ===============================
CREATE TABLE IF NOT EXISTS intent_templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    intent_name TEXT,
    template_text TEXT,
    is_active INTEGER DEFAULT 1
);

-- ===============================
-- CONVERSATION LOG
-- ===============================
CREATE TABLE IF NOT EXISTS conversation_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT,
    raw_text TEXT,
    normalized_text TEXT,
    intent TEXT,
    response_source TEXT,
    reply_text TEXT,
    model_name TEXT,
    latency_ms INTEGER,
    memory_context_used INTEGER,
    status TEXT,
    error_text TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- ===============================
-- LLM CALLS
-- ===============================
CREATE TABLE IF NOT EXISTS llm_calls (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT,
    intent TEXT,
    model_name TEXT,
    prompt_chars INTEGER,
    response_chars INTEGER,
    latency_ms INTEGER,
    status TEXT,
    error_text TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- ===============================
-- DAILY METRICS
-- ===============================
CREATE TABLE IF NOT EXISTS daily_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    metric_date TEXT,
    intent TEXT,
    response_source TEXT,
    total_count INTEGER,
    avg_latency_ms REAL,
    llm_count INTEGER,
    error_count INTEGER,
    UNIQUE(metric_date, intent, response_source)
);

-- ===============================
-- SYSTEM EVENTS
-- ===============================
CREATE TABLE IF NOT EXISTS system_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT,
    detail_text TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- ===============================
-- CONVERSATION TELEMETRY
-- ===============================
CREATE TABLE IF NOT EXISTS conversation_telemetry (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT,
    intent TEXT,
    response_source TEXT,
    model_name TEXT,
    latency_ms INTEGER,
    memory_context_used INTEGER,
    status TEXT,
    error_text TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- ===============================
-- RETRIEVAL DEBUG
-- ===============================
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
);

-- ===============================
-- STREAMING DEBUG
-- ===============================
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
);
