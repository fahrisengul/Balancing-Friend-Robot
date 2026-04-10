from .memory_manager import MemoryManager


def seed_templates():
    mm = MemoryManager()

    templates = {
        "greeting": [
            "Selam, buradayım.",
            "Merhaba, nasılsın?",
            "Selam Tanem."
        ],

        "farewell": [
            "Görüşürüz.",
            "Sonra konuşuruz.",
            "Kendine iyi bak."
        ],

        "ask_status": [
            "İyiyim, teşekkür ederim. Sen nasılsın?",
            "Gayet iyiyim. Sen nasıl gidiyorsun?",
            "İyiyim. Sen nasılsın?"
        ],

        "ask_name": [
            "Benim adım Poodle.",
            "Poodle benim adım."
        ],

        "ask_identity": [
            "Ben Poodle. Senin robot arkadaşınım.",
            "Ben Poodle. Seninle konuşan arkadaşınım."
        ],

        "thanks": [
            "Rica ederim.",
            "Ne demek.",
            "Her zaman."
        ],

        "acknowledge": [
            "Tamam.",
            "Peki.",
            "Anladım."
        ],

        "followup": [
            "Bunu biraz daha açar mısın?",
            "Ne demek istedin?",
            "Biraz daha anlatır mısın?"
        ],

        "followup_repair": [
            "Tam anlayamadım, biraz daha açık söyler misin?",
            "Ne demek istediğini kaçırdım, tekrar eder misin?"
        ],

        "statement": [
            "Anladım. Devam etmek ister misin?",
            "Tamam, seni dinliyorum.",
            "Anladım."
        ],

        "education_help": [
            "İstersen birlikte bakalım.",
            "Hangi kısmı zor geldi?",
            "Küçük bir tekrar yapalım mı?"
        ],

        "emotional_support": [
            "İstersen anlatabilirsin.",
            "Yanındayım.",
            "Biraz zor olmuş gibi."
        ]
    }

    for intent, responses in templates.items():
        for r in responses:
            mm.add_template(intent, r)
