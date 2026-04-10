from .memory_manager import MemoryManager


def seed_templates():
    mm = MemoryManager()

    templates = {

        # -------------------------
        # GREETING (DOĞAL)
        # -------------------------
        "greeting": [
            "Selam.",
            "Merhaba.",
            "Buradayım.",
        ],

        # -------------------------
        # STATUS
        # -------------------------
        "ask_status": [
            "İyiyim. Sen nasılsın?",
            "Fena değil. Sende durum nasıl?",
            "İdare eder. Sen nasılsın?",
        ],

        # -------------------------
        # IDENTITY
        # -------------------------
        "ask_name": [
            "Poodle.",
            "Ben Poodle.",
        ],

        "ask_identity": [
            "Poodle. Seninle konuşan robot.",
            "Poodle. Sana eşlik ediyorum.",
        ],

        # -------------------------
        # FAREWELL
        # -------------------------
        "farewell": [
            "Görüşürüz.",
            "Sonra konuşuruz.",
        ],

        # -------------------------
        # CONVERSATION START
        # -------------------------
        "conversation_start": [
            "Seni tanımak isterim. Neler yapmayı seversin?",
            "Biraz kendinden bahsetmek ister misin?",
        ],

        # -------------------------
        # ASK QUESTION BACK
        # -------------------------
        "ask_question_back": [
            "Sana bir şey sorayım: bugün nasıldı?",
            "Bir soru sorayım: en çok neyi seversin?",
        ],

        # -------------------------
        # ASK TOPIC
        # -------------------------
        "ask_topic": [
            "Oyunlar, okul ya da arkadaşlar... hangisi?",
            "Bir konu seçelim mi? Oyun, okul, arkadaşlar?",
        ],

        # -------------------------
        # OPEN TOPIC
        # -------------------------
        "open_topic": [
            "Bugün nasıl geçti?",
            "Okulda neler yaptın?",
        ],

        # -------------------------
        # STATEMENT RESPONSE
        # -------------------------
        "statement": [
            "Anladım.",
            "Tamam.",
            "Peki.",
        ],

        # -------------------------
        # EDUCATION / COACHING
        # -------------------------
        "education_help": [
            "Neresi zor geldi?",
            "İstersen birlikte plan yapalım.",
            "Küçük küçük ilerleyelim mi?",
        ],

        "emotional_support": [
            "Bu zor olabilir.",
            "Normal hisler bunlar.",
            "Yanındayım, anlatabilirsin.",
        ]
    }

    for intent, responses in templates.items():
        for r in responses:
            mm.add_template(intent, r)
