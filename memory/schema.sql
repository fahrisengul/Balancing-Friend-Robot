PRAGMA foreign_keys = ON;

-- -------------------------------------------------
-- PERSON PROFILES
-- -------------------------------------------------
CREATE TABLE IF NOT EXISTS person_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    role TEXT UNIQUE NOT NULL,
    birth_date TEXT,
    school_name TEXT,
    grade_level TEXT,
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- -------------------------------------------------
-- EPISODIC MEMORIES
-- -------------------------------------------------
CREATE TABLE IF NOT EXISTS episodic_memories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    person_id INTEGER,
    memory_text TEXT NOT NULL,
    category TEXT DEFAULT 'general',
    importance INTEGER DEFAULT 1,
    tags_json TEXT DEFAULT '[]',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (person_id) REFERENCES person_profiles(id) ON DELETE SET NULL
);

-- -------------------------------------------------
-- INTENT DEFINITIONS
-- -------------------------------------------------
CREATE TABLE IF NOT EXISTS intent_definitions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    intent_name TEXT UNIQUE NOT NULL,
    category TEXT DEFAULT 'general',
    source_preference TEXT DEFAULT 'llm', -- template / llm / hybrid / skill
    priority INTEGER DEFAULT 0,
    is_active INTEGER DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- -------------------------------------------------
-- INTENT PATTERNS
-- -------------------------------------------------
CREATE TABLE IF NOT EXISTS intent_patterns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    intent_name TEXT NOT NULL,
    pattern_text TEXT NOT NULL,
    match_type TEXT DEFAULT 'contains', -- contains / exact / starts_with
    lang TEXT DEFAULT 'tr',
    priority INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- -------------------------------------------------
-- INTENT TEMPLATES
-- -------------------------------------------------
CREATE TABLE IF NOT EXISTS intent_templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    intent_name TEXT NOT NULL,
    template_text TEXT NOT NULL,
    tone TEXT DEFAULT 'neutral',
    lang TEXT DEFAULT 'tr',
    priority INTEGER DEFAULT 0,
    is_active INTEGER DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- -------------------------------------------------
-- INTENT FOLLOWUPS
-- -------------------------------------------------
CREATE TABLE IF NOT EXISTS intent_followups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    intent_name TEXT NOT NULL,
    followup_text TEXT NOT NULL,
    priority INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- -------------------------------------------------
-- INDEXES
-- -------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_person_profiles_role
ON person_profiles(role);

CREATE INDEX IF NOT EXISTS idx_episodic_memories_person_id
ON episodic_memories(person_id);

CREATE INDEX IF NOT EXISTS idx_intent_patterns_intent_name
ON intent_patterns(intent_name);

CREATE INDEX IF NOT EXISTS idx_intent_templates_intent_name
ON intent_templates(intent_name);

CREATE INDEX IF NOT EXISTS idx_intent_followups_intent_name
ON intent_followups(intent_name);
