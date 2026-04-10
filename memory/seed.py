from .db import init_db, get_connection
from .memory_manager import MemoryManager


def seed_profiles():
    mm = MemoryManager()

    tanem = mm.get_person_by_role("tanem")
    if tanem is None:
        mm.create_person_profile(
            name="Tanem",
            role="tanem",
            birth_date="2013-05-30",
            school_name="Sınav Koleji",
            grade_level="5",
            notes="Ana kullanıcı profili. Çocuk dostu, destekleyici ve güvenli konuşma tercih edilmeli."
        )

    print(">>> Profiles seeded.")


def seed_intents():
    mm = MemoryManager()

    intent_definitions = [
        ("greeting", "social", "template", 100),
        ("farewell", "social", "template", 100),
        ("ask_name", "social", "template", 95),
        ("ask_identity", "social", "template", 95),
        ("ask_status", "social", "template", 95),
        ("thanks", "social", "template", 90),
        ("acknowledge", "social", "template", 80),
        ("followup", "social", "template", 85),
        ("followup_repair", "social", "template", 85),
        ("ask_user_profile", "social", "llm", 92),
        ("request_questioning", "social", "llm", 92),
        ("topic_suggestion", "social", "template", 88),
        ("ask_activity", "social", "llm", 88),
        ("education_help", "education", "llm", 90),
        ("emotional_support", "emotion", "llm", 90),
        ("question", "general", "llm", 70),
        ("statement", "general", "llm", 60),
        ("general", "general", "llm", 50),
        ("mute", "utility", "skill", 100),
        ("wake", "utility", "skill", 100),
    ]

    patterns = [
        # greeting
        ("greeting", "selam", "contains", "tr", 100),
        ("greeting", "merhaba", "contains", "tr", 100),
        ("greeting", "hey", "exact", "tr", 80),

        # farewell
        ("farewell", "gorusuruz", "contains", "tr", 100),
        ("farewell", "hoşça kal", "contains", "tr", 100),
        ("farewell", "hosca kal", "contains", "tr", 100),
        ("farewell", "bay bay", "contains", "tr", 90),

        # ask_name
        ("ask_name", "adin ne", "contains", "tr", 100),
        ("ask_name", "adın ne", "contains", "tr", 100),

        # ask_identity
        ("ask_identity", "kimsin", "contains", "tr", 100),
        ("ask_identity", "kendini tanimlar misin", "contains", "tr", 100),
        ("ask_identity", "kendini tanımlar mısın", "contains", "tr", 100),

        # ask_status
        ("ask_status", "nasilsin", "contains", "tr", 100),
        ("ask_status", "nasılsın", "contains", "tr", 100),

        # thanks
        ("thanks", "tesekkur", "contains", "tr", 100),
        ("thanks", "teşekkür", "contains", "tr", 100),

        # acknowledge
        ("acknowledge", "tamam", "exact", "tr", 100),
        ("acknowledge", "peki", "exact", "tr", 100),
        ("acknowledge", "olur", "exact", "tr", 100),

        # ask_user_profile
        ("ask_user_profile", "benimle ilgili ne biliyorsun", "contains", "tr", 100),
        ("ask_user_profile", "benim hakkimda ne biliyorsun", "contains", "tr", 100),
        ("ask_user_profile", "benim hakkımda ne biliyorsun", "contains", "tr", 100),

        # request_questioning
        ("request_questioning", "bana soru sor", "contains", "tr", 100),
        ("request_questioning", "beni tanimak ister misin", "contains", "tr", 100),
        ("request_questioning", "beni tanımak ister misin", "contains", "tr", 100),
        ("request_questioning", "beni tanimak icin sorular sorar misin", "contains", "tr", 100),
        ("request_questioning", "beni tanımak için sorular sorar mısın", "contains", "tr", 100),

        # topic_suggestion
        ("topic_suggestion", "ne konusalim", "contains", "tr", 100),
        ("topic_suggestion", "ne konuşalım", "contains", "tr", 100),
        ("topic_suggestion", "konu ac", "contains", "tr", 100),
        ("topic_suggestion", "konu aç", "contains", "tr", 100),

        # ask_activity
        ("ask_activity", "neler yapiyorsun", "contains", "tr", 100),
        ("ask_activity", "neler yapıyorsun", "contains", "tr", 100),
        ("ask_activity", "ne yapiyorsun", "contains", "tr", 100),
        ("ask_activity", "ne yapıyorsun", "contains", "tr", 100),

        # education_help
        ("education_help", "sinav", "contains", "tr", 100),
        ("education_help", "sınav", "contains", "tr", 100),
        ("education_help", "ders", "contains", "tr", 95),
        ("education_help", "matematik", "contains", "tr", 95),
        ("education_help", "lgs", "contains", "tr", 95),
        ("education_help", "endise azaltici", "contains", "tr", 95),
        ("education_help", "endişe azaltıcı", "contains", "tr", 95),

        # emotional_support
        ("emotional_support", "uzgunum", "contains", "tr", 100),
        ("emotional_support", "üzgünüm", "contains", "tr", 100),
        ("emotional_support", "moralim bozuk", "contains", "tr", 100),
        ("emotional_support", "kotu hissediyorum", "contains", "tr", 100),
        ("emotional_support", "kötü hissediyorum", "contains", "tr", 100),

        # mute / wake
        ("mute", "sus", "exact", "tr", 100),
        ("mute", "dur", "exact", "tr", 90),
        ("mute", "sessiz ol", "exact", "tr", 100),
        ("wake", "hey poodle", "contains", "tr", 100),
        ("wake", "hey puddle", "contains", "tr", 90),
        ("wake", "hey pudil", "contains", "tr", 90),
        ("wake", "poodle", "exact", "tr", 70),
    ]

    templates = {
        "greeting": [
            ("Selam.", "warm", 100),
            ("Merhaba.", "warm", 95),
            ("Selam, buradayım.", "warm", 90),
        ],
        "farewell": [
            ("Görüşürüz.", "neutral", 100),
            ("Sonra konuşuruz.", "warm", 90),
            ("Kendine iyi bak.", "warm", 85),
        ],
        "ask_name": [
            ("Benim adım Poodle.", "neutral", 100),
            ("Poodle benim adım.", "neutral", 90),
        ],
        "ask_identity": [
            ("Ben Poodle. Seninle konuşan robot arkadaşınım.", "warm", 100),
            ("Ben Poodle. Sana eşlik eden sakin bir robot arkadaşım.", "warm", 90),
        ],
        "ask_status": [
            ("İyiyim, teşekkür ederim. Sen nasılsın?", "warm", 100),
            ("Gayet iyiyim. Sen nasılsın?", "warm", 95),
            ("İyiyim. Sen nasıl gidiyorsun?", "warm", 85),
        ],
        "thanks": [
            ("Rica ederim.", "warm", 100),
            ("Ne demek.", "neutral", 90),
            ("Her zaman.", "warm", 85),
        ],
        "acknowledge": [
            ("Tamam.", "neutral", 100),
            ("Peki.", "neutral", 95),
        ],
        "followup": [
            ("Bunu biraz daha açar mısın?", "neutral", 100),
            ("Ne demek istediğini biraz daha anlatır mısın?", "neutral", 90),
        ],
        "followup_repair": [
            ("Tam anlayamadım, biraz daha açık söyler misin?", "neutral", 100),
            ("Ne demek istediğini kaçırdım, tekrar eder misin?", "neutral", 90),
        ],
        "topic_suggestion": [
            ("İstersen okuldan, oyunlardan ya da hayallerinden konuşabiliriz.", "warm", 100),
            ("İstersen bugün nasıl geçtiğinden başlayabiliriz.", "warm", 90),
        ],
    }

    followups = {
        "request_questioning": [
            ("En sevdiğin şey nedir?", 100),
            ("Bugün seni en çok ne mutlu etti?", 95),
            ("Şu sıralar en çok neyle ilgileniyorsun?", 90),
        ],
        "ask_user_profile": [
            ("Şu an seni biraz tanıyorum, ama daha fazlasını öğrenebilirim.", 100),
        ],
        "education_help": [
            ("İstersen bunu küçük adımlara bölelim.", 100),
            ("İstersen önce en zor kısmı seçelim.", 95),
        ],
        "emotional_support": [
            ("İstersen bunu birlikte sakin sakin konuşabiliriz.", 100),
            ("İstersen önce seni en çok zorlayan kısmı söyle.", 95),
        ],
    }

    with get_connection() as conn:
        for intent_name, category, source_preference, priority in intent_definitions:
            conn.execute(
                """
                INSERT OR IGNORE INTO intent_definitions
                (intent_name, category, source_preference, priority, is_active)
                VALUES (?, ?, ?, ?, 1)
                """,
                (intent_name, category, source_preference, priority),
            )

        for intent_name, pattern_text, match_type, lang, priority in patterns:
            existing = conn.execute(
                """
                SELECT 1
                FROM intent_patterns
                WHERE intent_name = ?
                  AND pattern_text = ?
                  AND match_type = ?
                  AND lang = ?
                LIMIT 1
                """,
                (intent_name, pattern_text, match_type, lang),
            ).fetchone()

            if not existing:
                conn.execute(
                    """
                    INSERT INTO intent_patterns
                    (intent_name, pattern_text, match_type, lang, priority)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (intent_name, pattern_text, match_type, lang, priority),
                )

        for intent_name, rows in templates.items():
            for template_text, tone, priority in rows:
                existing = conn.execute(
                    """
                    SELECT 1
                    FROM intent_templates
                    WHERE intent_name = ?
                      AND template_text = ?
                      AND lang = 'tr'
                    LIMIT 1
                    """,
                    (intent_name, template_text),
                ).fetchone()

                if not existing:
                    conn.execute(
                        """
                        INSERT INTO intent_templates
                        (intent_name, template_text, tone, lang, priority, is_active)
                        VALUES (?, ?, ?, 'tr', ?, 1)
                        """,
                        (intent_name, template_text, tone, priority),
                    )

        for intent_name, rows in followups.items():
            for followup_text, priority in rows:
                existing = conn.execute(
                    """
                    SELECT 1
                    FROM intent_followups
                    WHERE intent_name = ?
                      AND followup_text = ?
                    LIMIT 1
                    """,
                    (intent_name, followup_text),
                ).fetchone()

                if not existing:
                    conn.execute(
                        """
                        INSERT INTO intent_followups
                        (intent_name, followup_text, priority)
                        VALUES (?, ?, ?)
                        """,
                        (intent_name, followup_text, priority),
                    )

        conn.commit()

    print(">>> Intents seeded.")


def run_all():
    init_db()
    seed_profiles()
    seed_intents()


if __name__ == "__main__":
    run_all()
