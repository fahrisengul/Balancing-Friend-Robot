from memory.memory_manager import MemoryManager


def run_all():
    mm = MemoryManager()

    seed_intents(mm)
    seed_patterns(mm)
    seed_templates(mm)

    print(">>> Seed tamamlandı.")


# -------------------------
# INTENTS
# -------------------------

def seed_intents(mm):
    intents = [
        "greeting",
        "identity",
        "ask_name",
        "smalltalk_howareyou",
        "request_questioning",
        "topic_suggestion",
        "exam_anxiety",
        "request_advice",
        "post_exam_reflection",
        "fallback",
    ]

    for intent in intents:
        mm.add_intent_if_missing(intent)


# -------------------------
# PATTERNS
# -------------------------

def seed_patterns(mm):
    patterns = [
        # greeting
        ("greeting", r"\b(selam|merhaba|hey)\b"),

        # identity
        ("identity", r"\b(kimsin|kendini tanıt)\b"),

        # ask name
        ("ask_name", r"\b(adın ne)\b"),

        # how are you
        ("smalltalk_howareyou", r"\b(nasılsın)\b"),

        # questioning
        ("request_questioning", r"\b(bana soru sor|beni tanımak)\b"),

        # topic suggestion
        ("topic_suggestion", r"\b(ne konuşalım|konu aç|hakkında konuşalım)\b"),

        # anxiety
        ("exam_anxiety", r"\b(sınav.*endişe|stresliyim)\b"),

        # advice
        ("request_advice", r"\b(öner|yöntem)\b"),

        # reflection
        ("post_exam_reflection", r"\b(iyi geçmedi|neden böyle)\b"),
    ]

    for intent, pattern in patterns:
        mm.add_pattern_if_missing(intent, pattern)


# -------------------------
# TEMPLATES
# -------------------------

def seed_templates(mm):
    templates = [
        ("greeting", "Selam."),
        ("smalltalk_howareyou", "İyiyim. Sen nasılsın?"),
        ("fallback", "Seni tam anlayamadım. Biraz daha açık söyler misin?"),
    ]

    for intent, text in templates:
        mm.add_template_if_missing(intent, text)
