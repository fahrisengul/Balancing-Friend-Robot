from .db import init_db, get_connection
from .memory_manager import MemoryManager


# =========================================================
# INTENT PATTERNS
# =========================================================
def get_intent_patterns():
    return [

        # BASIC
        ("greeting", ["merhaba", "selam", "hey"]),
        ("farewell", ["görüşürüz", "bye", "hoşçakal"]),
        ("ask_name", ["adın ne", "senin adın ne"]),
        ("ask_status", ["nasılsın", "iyi misin"]),
        ("thanks", ["teşekkür", "sağol", "sagol"]),

        ("ask_user_name", ["benim adım ne", "adımı biliyor musun"]),
        ("user_name_define", ["bana * diyebilirsin", "benim adım *"]),

        # SYSTEM
        ("audio_check", [
            "beni duyabiliyor musun",
            "beni duyabiliyormusun",
            "duyuyor musun",
        ]),

        # EDUCATION
        ("education_topics", [
            "lgs konuları",
            "matematik konuları",
            "ders konuları",
            "hangi konular",
            "konuları listeler misin",
            "hangi konulara çalışmalıyım",
            "hangi konulara odaklanmalıyım",
        ]),

        ("exam_support", [
            "sınav stresi",
            "sınav hakkında",
            "lgs hakkında",
            "nasıl çalışmalıyım",
            "nasıl ders çalışılır",
        ]),

        ("concept_explanation", [
            "nedir",
            "ne demek",
            "anlatır mısın",
            "detay verir misin",
        ]),

        ("education_planning", [
            "çalışma planı",
            "nasıl program yaparım",
            "ders planı",
        ]),

        # META
        ("ask_identity", ["sen kimsin"]),
        ("conversation_start", ["konuşalım"]),
        ("open_topic", ["bir şey anlat"]),
    ]


# =========================================================
# TEMPLATE TEXTS
# =========================================================
def get_templates():
    return [

        ("greeting", "Selam!"),
        ("farewell", "Görüşürüz."),
        ("ask_name", "Ben Poodle."),
        ("ask_status", "İyiyim. Sen nasılsın?"),
        ("thanks", "Rica ederim."),
        ("ask_user_name", "Adını henüz bilmiyorum. Söylersen hatırlarım."),
        ("user_name_define", "Tamam. Sana {name} diyeyim."),
        ("audio_check", "Evet, seni duyuyorum."),

        # EDUCATION
        ("education_topics",
         "İstersen ana konuları birlikte netleştirebiliriz. Matematikte sayılar, cebir ve problemler önemli."),

        ("exam_support",
         "Sınav stresi normal. İstersen bunu birlikte daha rahat yönetebiliriz."),

        ("concept_explanation",
         "İstersen bunu kısa ve sade şekilde anlatayım."),

        ("education_planning",
         "İstersen sana basit bir çalışma planı oluşturabilirim."),

        # META
        ("ask_identity", "Ben sana yardımcı olmaya çalışan bir robot arkadaşım."),
        ("conversation_start", "Tamam. Ne hakkında konuşalım?"),
        ("open_topic", "İstersen sana bir konu önerebilirim."),
    ]


# =========================================================
# SEED LOAD
# =========================================================
def seed_database():
    print(">>> [SEED] Başlatılıyor...")

    init_db()
    mm = MemoryManager()

    with get_connection() as conn:

        # INTENTS
        for intent_name, patterns in get_intent_patterns():
            conn.execute(
                """
                INSERT OR IGNORE INTO intent_definitions (name)
                VALUES (?)
                """,
                (intent_name,),
            )

            for p in patterns:
                conn.execute(
                    """
                    INSERT INTO intent_patterns (intent_name, pattern)
                    VALUES (?, ?)
                    """,
                    (intent_name, p),
                )

        # TEMPLATES
        for intent_name, template_text in get_templates():
            conn.execute(
                """
                INSERT INTO intent_templates (intent_name, template_text, is_active)
                VALUES (?, ?, 1)
                """,
                (intent_name, template_text),
            )

        conn.commit()

    print(">>> [SEED] Tamamlandı.")
