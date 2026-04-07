from .memory_manager import MemoryManager


def seed_profiles():
    mm = MemoryManager()

    # Ana kullanıcı profili
    tanem = mm.get_person_by_role("tanem")
    if not tanem:
        mm.create_person_profile(
            name="Tanem",
            role="tanem",
            birth_date="2013-05-30",
            school_name=None,
            grade_level=None,
            notes="Ana kullanıcı profili"
        )

    print(">>> Profiles seeded.")


def seed_templates():
    mm = MemoryManager()

    templates = [
        # greeting
        ("greeting", "Selam, ben Poodle.", "warm", "tr", 10, True),
        ("greeting", "Merhaba, ben Poodle.", "neutral", "tr", 9, True),
        ("greeting", "Selam, buradayım.", "warm", "tr", 10, True),

        # ask_name
        ("ask_name", "Benim adım Poodle.", "neutral", "tr", 10, True),

        # ask_identity
        ("ask_identity", "Ben seninle konuşan robot arkadaşınım.", "warm", "tr", 10, True),

        # ask_status
        ("ask_status", "İyiyim, teşekkür ederim. Sen nasılsın?", "warm", "tr", 10, True),
        ("ask_status", "Gayet iyiyim. Sen nasılsın?", "neutral", "tr", 9, True),

        # thanks
        ("thanks", "Rica ederim.", "neutral", "tr", 10, True),
        ("thanks", "Ne demek.", "warm", "tr", 8, True),

        # acknowledge
        ("acknowledge", "Tamam.", "neutral", "tr", 10, True),
        ("acknowledge", "Peki.", "neutral", "tr", 8, True),

        # clarify
        ("clarify", "Seni tam anlayamadım. Bir kez daha söyler misin?", "neutral", "tr", 10, True),
        ("clarify", "Son söylediğini tam çıkaramadım. Bir daha söyler misin?", "warm", "tr", 9, True),

        # followup
        ("followup", "Bunu biraz daha açar mısın?", "neutral", "tr", 10, True),
        ("followup", "Biraz daha açık anlatır mısın?", "neutral", "tr", 9, True),

        # smalltalk_short
        ("smalltalk_short", "Anladım.", "neutral", "tr", 10, True),
        ("smalltalk_short", "Tamam, anladım.", "neutral", "tr", 9, True),

        ("farewell", "Görüşürüz.", "neutral", "tr", 10, True),
        ("followup_repair", "Tam olarak neyi sormak istemiştin?", "neutral", "tr", 10, True),
    ]

    for intent_name, template_text, tone, lang, priority, is_active in templates:
        _insert_template_if_missing(
            mm=mm,
            intent_name=intent_name,
            template_text=template_text,
            tone=tone,
            lang=lang,
            priority=priority,
            is_active=is_active,
        )

    print(">>> Templates seeded.")


def seed_memories():
    mm = MemoryManager()

    tanem = mm.get_person_by_role("tanem")
    tanem_id = tanem["id"] if tanem else None

    if tanem_id is not None:
        default_memories = [
            ("Tanem voleybol ile ilgileniyor.", "interest", 2, ["voleybol", "spor"]),
            ("Tanem'in doğum günü 30 Mayıs.", "milestone", 3, ["doğum günü", "30 mayıs"]),
            ("Robot kısa, doğal ve güven veren şekilde konuşmalı.", "interaction", 3, ["iletişim", "kısa cevap"]),
        ]

        for text, category, importance, tags in default_memories:
            _insert_memory_if_missing(
                mm=mm,
                person_id=tanem_id,
                memory_text=text,
                category=category,
                importance=importance,
                tags=tags,
            )

    print(">>> Memories seeded.")


def run_all():
    seed_profiles()
    seed_templates()
    seed_memories()
    print(">>> Seed completed.")


def _insert_template_if_missing(mm, intent_name, template_text, tone, lang, priority, is_active):
    from .db import get_connection

    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT id
            FROM intent_templates
            WHERE intent_name = ?
              AND template_text = ?
              AND lang = ?
            LIMIT 1
            """,
            (intent_name, template_text, lang),
        ).fetchone()

    if row:
        return

    mm.add_template(
        intent_name=intent_name,
        template_text=template_text,
        tone=tone,
        lang=lang,
        priority=priority,
        is_active=is_active,
    )


def _insert_memory_if_missing(mm, person_id, memory_text, category, importance, tags):
    from .db import get_connection

    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT id
            FROM episodic_memories
            WHERE person_id = ?
              AND memory_text = ?
            LIMIT 1
            """,
            (person_id, memory_text),
        ).fetchone()

    if row:
        return

    mm.add_episodic_memory(
        memory_text=memory_text,
        person_id=person_id,
        category=category,
        importance=importance,
        tags=tags,
    )


if __name__ == "__main__":
    run_all()
