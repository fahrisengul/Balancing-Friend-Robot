PRAGMA foreign_keys = ON;

-- =========================================================
-- person_profiles
-- Kim kimdir?
-- Tanem, arkadaşları, aile üyeleri vb.
-- =========================================================
CREATE TABLE IF NOT EXISTS person_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'unknown', -- tanem, friend, parent, teacher, unknown
    birth_date TEXT,                      -- YYYY-MM-DD
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
-- Günlük öğrenilen olaylar
-- =========================================================
CREATE TABLE IF NOT EXISTS episodic_memories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    person_id INTEGER,
    memory_text TEXT NOT NULL,
    category TEXT NOT NULL DEFAULT 'general', -- general, school, emotion, relationship, education
    importance INTEGER NOT NULL DEFAULT 1,    -- 1..5
    tags_json TEXT,                           -- JSON string
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

-- =========================================================
-- intent_templates
-- Kısa / deterministic cevaplar
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
-- Debug, kalite izleme ve geliştirme
-- =========================================================
CREATE TABLE IF NOT EXISTS conversation_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    raw_text TEXT,
    normalized_text TEXT,
    intent TEXT,
    response_source TEXT,  -- clarify, skill, template, llm
    reply_text TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_conversation_logs_intent
ON conversation_logs(intent);

CREATE INDEX IF NOT EXISTS idx_conversation_logs_response_source
ON conversation_logs(response_source);
