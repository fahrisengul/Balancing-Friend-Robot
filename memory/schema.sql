PRAGMA foreign_keys = ON;

-- =========================================================
-- person_profiles
-- =========================================================
CREATE TABLE IF NOT EXISTS person_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'unknown',
    birth_date TEXT,
    school_name TEXT,
    grade_level TEXT,
    notes TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_person_profiles_name
ON person_profiles(name);

CREATE INDEX IF NOT EXISTS idx_person_profiles_role
ON person_profiles(role);

-- =========================================================
-- episodic_memories
-- =========================================================
CREATE TABLE IF NOT EXISTS episodic_memories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    person_id INTEGER,
    memory_text TEXT NOT NULL,
    category TEXT NOT NULL DEFAULT 'general',
    importance INTEGER NOT NULL DEFAULT 1,
    tags_json TEXT,
    source TEXT NOT NULL DEFAULT 'conversation',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_used_at TEXT,
    FOREIGN KEY (person_id) REFERENCES person_profiles(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_episodic_memories_person_id
ON episodic_memories(person_id);

CREATE INDEX IF NOT EXISTS idx_episodic_memories_category
ON episodic_memories(category);

CREATE INDEX IF NOT EXISTS idx_episodic_memories_importance
ON episodic_memories(importance);

CREATE INDEX IF NOT EXISTS idx_episodic_memories_created_at
ON episodic_memories(created_at);

-- =========================================================
-- intent_templates
-- =========================================================
CREATE TABLE IF NOT EXISTS intent_templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    intent_name TEXT NOT NULL,
    template_text TEXT NOT NULL,
    tone TEXT NOT NULL DEFAULT 'neutral',
    lang TEXT NOT NULL DEFAULT 'tr',
    priority INTEGER NOT NULL DEFAULT 1,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_intent_templates_intent_name
ON intent_templates(intent_name);

CREATE INDEX IF NOT EXISTS idx_intent_templates_active
ON intent_templates(is_active);

-- =========================================================
-- conversation_logs
-- Hafif, kullanıcı ve cevap odaklı ana log
-- =========================================================
CREATE TABLE IF NOT EXISTS conversation_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT,
    raw_text TEXT,
    normalized_text TEXT,
    intent TEXT,
    response_source TEXT,          -- clarify, skill, template, education, llm
    reply_text TEXT,
    model_name TEXT,
    latency_ms INTEGER,
    memory_context_used INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'ok',   -- ok, error
    error_text TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_conversation_logs_session_id
ON conversation_logs(session_id);

CREATE INDEX IF NOT EXISTS idx_conversation_logs_intent
ON conversation_logs(intent);

CREATE INDEX IF NOT EXISTS idx_conversation_logs_response_source
ON conversation_logs(response_source);

CREATE INDEX IF NOT EXISTS idx_conversation_logs_created_at
ON conversation_logs(created_at);

-- =========================================================
-- llm_calls
-- Sadece LLM telemetrisi
-- =========================================================
CREATE TABLE IF NOT EXISTS llm_calls (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT,
    intent TEXT,
    model_name TEXT NOT NULL,
    prompt_chars INTEGER NOT NULL DEFAULT 0,
    response_chars INTEGER NOT NULL DEFAULT 0,
    latency_ms INTEGER,
    status TEXT NOT NULL DEFAULT 'ok',   -- ok, error
    error_text TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_llm_calls_session_id
ON llm_calls(session_id);

CREATE INDEX IF NOT EXISTS idx_llm_calls_intent
ON llm_calls(intent);

CREATE INDEX IF NOT EXISTS idx_llm_calls_created_at
ON llm_calls(created_at);

-- =========================================================
-- daily_metrics
-- Uzun süreli küçük özet tablo
-- =========================================================
CREATE TABLE IF NOT EXISTS daily_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    metric_date TEXT NOT NULL,           -- YYYY-MM-DD
    intent TEXT,
    response_source TEXT,
    total_count INTEGER NOT NULL DEFAULT 0,
    avg_latency_ms REAL,
    avg_reply_chars REAL,
    llm_count INTEGER NOT NULL DEFAULT 0,
    error_count INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(metric_date, intent, response_source)
);

CREATE INDEX IF NOT EXISTS idx_daily_metrics_metric_date
ON daily_metrics(metric_date);

-- =========================================================
-- system_events
-- Cleanup, migration, export, boot gibi teknik olaylar
-- =========================================================
CREATE TABLE IF NOT EXISTS system_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT NOT NULL,            -- boot, cleanup, export, migration
    detail_text TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_system_events_event_type
ON system_events(event_type);

CREATE INDEX IF NOT EXISTS idx_system_events_created_at
ON system_events(created_at);
