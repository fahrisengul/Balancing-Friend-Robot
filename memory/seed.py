from .memory_manager import MemoryManager


def seed_templates():
    mm = MemoryManager()

    templates = {

        # -------------------------
        # BASIC
        # -------------------------
        "greeting": [
            "Selam, buradayım.",
            "Merhaba, nasılsın?",
        ],

        "farewell": [
            "Görüşürüz.",
            "Sonra konuşuruz.",
        ],

        "ask_status": [
            "İyiyim. Sen nasılsın?",
        ],

        "ask_name": [
            "Benim adım Poodle.",
        ],

        "ask_identity": [
            "Ben Poodle. Senin robot arkadaşınım.",
        ],

        # -------------------------
        # 🚀 NEW CRITICAL INTENTS
        # -------------------------
        "conversation_start": [
            "Seni tanımak isterim. Bana biraz kendinden bahseder misin?",
            "Seninle tanışmak güzel. Neler yapmayı seversin?",
        ],

        "ask_question_back": [
            "Sana bir soru sorayım: bugün seni en çok ne zorladı?",
            "Bugün seni mutlu eden bir şey oldu mu?",
        ],

        "ask_topic": [
            "İstersen oyunlar, okul ya da arkadaşlar hakkında konuşabiliriz.",
            "Hangi konuyu seçmek istersin?",
        ],

        "open_topic": [
            "Bugün okulda nasıldı?",
            "Bugün ilginç bir şey yaşadın mı?",
        ],

        # -------------------------
        # COACHING
        # -------------------------
        "education_help": [
            "Hangi kısmı zor geldi?",
            "Birlikte küçük bir plan yapalım mı?",
        ],

        "emotional_support": [
            "Bu zor hissettirmiş olabilir.",
            "Yanındayım, anlatabilirsin.",
        ]
    }

    for intent, responses in templates.items():
        for r in responses:
            mm.add_template(intent, r)
