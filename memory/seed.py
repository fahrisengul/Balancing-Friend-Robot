from .db import init_db, get_connection
from .memory_manager import MemoryManager


def seed_profiles():
    mm = MemoryManager()

    tanem = None
    if hasattr(mm, "get_person_by_role"):
        tanem = mm.get_person_by_role("tanem")

    if tanem is None and hasattr(mm, "create_person_profile"):
        mm.create_person_profile(
            name="Tanem",
            role="tanem",
            birth_date="2013-05-30",
            school_name="Sınav Koleji",
            grade_level="5",
            notes="Ana kullanıcı profili. Çocuk dostu, sıcak ve kısa konuşma tercih edilir."
        )

    print(">>> Profiles seeded.")


def seed_intents():
    intent_definitions = [
        ("greeting", "social", "template", 100),
        ("farewell", "social", "template", 100),
        ("ask_name", "social", "template", 100),
        ("ask_identity", "social", "template", 98),
        ("ask_status", "social", "template", 100),
        ("thanks", "social", "template", 95),
        ("conversation_start", "social", "template", 95),
        ("ask_question_back", "social", "template", 95),
        ("ask_topic", "social", "template", 95),
        ("open_topic", "social", "template", 90),
        ("ask_user_name", "social", "template", 100),
        ("user_name_define", "social", "template", 100),
        ("general", "general", "llm", 50),
    ]

    patterns = [
        ("greeting", "merhaba", "contains", "tr", 100),
        ("greeting", "selam", "contains", "tr", 100),

        ("farewell", "görüşürüz", "contains", "tr", 100),
        ("farewell", "gorusuruz", "contains", "tr", 100),
        ("farewell", "hoşça kal", "contains", "tr", 100),
        ("farewell", "hosca kal", "contains", "tr", 100),

        ("ask_name", "senin adın ne", "contains", "tr", 100),
        ("ask_name", "senin adin ne", "contains", "tr", 100),
        ("ask_name", "adın ne", "contains", "tr", 90),
        ("ask_name", "adin ne", "contains", "tr", 90),

        ("ask_identity", "kimsin", "contains", "tr", 100),
        ("ask_identity", "kendini tanımlar mısın", "contains", "tr", 100),
        ("ask_identity", "kendini tanimlar misin", "contains", "tr", 100),

        ("ask_status", "nasılsın", "contains", "tr", 100),
        ("ask_status", "nasilsin", "contains", "tr", 100),
        ("ask_status", "iyi misin", "contains", "tr", 90),

        ("thanks", "teşekkür", "contains", "tr", 100),
        ("thanks", "tesekkur", "contains", "tr", 100),

        ("conversation_start", "konuşalım", "contains", "tr", 100),
        ("conversation_start", "konusalim", "contains", "tr", 100),

        ("ask_question_back", "bana soru sor", "contains", "tr", 100),
        ("ask_question_back", "bana soru sorar mısın", "contains", "tr", 100),
        ("ask_question_back", "bana soru sorar misin", "contains", "tr", 100),

        ("ask_topic", "ne konuşalım", "contains", "tr", 100),
        ("ask_topic", "ne konusalim", "contains", "tr", 100),

        ("open_topic", "başlayalım", "contains", "tr", 90),
        ("open_topic", "baslayalim", "contains", "tr", 90),

        ("ask_user_name", "benim adım nedir", "contains", "tr", 100),
        ("ask_user_name", "benim adim nedir", "contains", "tr", 100),
        ("ask_user_name", "adım ne", "contains", "tr", 90),
        ("ask_user_name", "adim ne", "contains", "tr", 90),

        ("user_name_define", "bana ", "contains", "tr", 80),
    ]

    templates = {
        "greeting": [
            ("Selam!", "warm", 100),
            ("Merhaba!", "warm", 95),
            ("Buradayım.", "warm", 90),
        ],
        "farewell": [
            ("Görüşürüz.", "warm", 100),
            ("Sonra konuşuruz.", "warm", 95),
        ],
        "ask_name": [
            ("Ben Poodle.", "warm", 100),
        ],
        "ask_identity": [
            ("Ben Poodle. Seninle konuşan robot arkadaşınım.", "warm", 100),
        ],
        "ask_status": [
            ("İyiyim. Sen nasılsın?", "warm", 100),
            ("İyiyim. Sende durum nasıl?", "warm", 95),
        ],
        "thanks": [
            ("Rica ederim.", "warm", 100),
            ("Ne demek.", "warm", 95),
        ],
        "conversation_start": [
            ("Tamam. Ne hakkında konuşalım?", "warm", 100),
        ],
        "ask_question_back": [
            ("Tabii. Bugün nasıl geçti?", "warm", 100),
        ],
        "ask_topic": [
            ("İstersen okul, oyunlar ya da arkadaşlar hakkında konuşabiliriz.", "warm", 100),
        ],
        "open_topic": [
            ("Tamam. Başlayalım.", "warm", 100),
        ],
        "ask_user_name": [
            ("Adını söylersen hatırlamaya çalışırım.", "warm", 100),
        ],
        "user_name_define": [
            ("Tamam. Öyle diyeyim.", "warm", 100),
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
            exists = conn.execute(
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

            if not exists:
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
                exists = conn.execute(
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

                if not exists:
                    conn.execute(
                        """
                        INSERT INTO intent_templates
                        (intent_name, template_text, tone, lang, priority, is_active)
                        VALUES (?, ?, ?, 'tr', ?, 1)
                        """,
                        (intent_name, template_text, tone, priority),
                    )

        conn.commit()

    print(">>> Intents seeded.")


def run_all():
    init_db()
    seed_profiles()
    seed_intents()


if __name__ == "__main__":
    run_all()
