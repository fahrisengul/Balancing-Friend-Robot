from .memory_manager import MemoryManager
from .db import init_db


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


def seed_templates():
    mm = MemoryManager()

    templates = {
        "greeting": [
            ("Selam, buradayım.", "warm", 10),
            ("Merhaba.", "warm", 9),
            ("Selam.", "warm", 8),
        ],
        "farewell": [
            ("Görüşürüz.", "neutral", 10),
            ("Sonra konuşuruz.", "warm", 8),
            ("Kendine iyi bak.", "warm", 7),
        ],
        "ask_status": [
            ("İyiyim, teşekkür ederim. Sen nasılsın?", "warm", 10),
            ("Gayet iyiyim. Sen nasılsın?", "warm", 9),
            ("İyiyim. Sen nasıl gidiyorsun?", "warm", 8),
        ],
        "ask_name": [
            ("Benim adım Poodle.", "neutral", 10),
            ("Poodle benim adım.", "neutral", 8),
        ],
        "ask_identity": [
            ("Ben Poodle. Senin robot arkadaşınım.", "warm", 10),
            ("Ben Poodle. Seninle konuşan arkadaşınım.", "warm", 8),
        ],
        "thanks": [
            ("Rica ederim.", "warm", 10),
            ("Ne demek.", "neutral", 8),
            ("Her zaman.", "warm", 7),
        ],
        "acknowledge": [
            ("Tamam.", "neutral", 10),
            ("Peki.", "neutral", 9),
        ],
        "followup": [
            ("Bunu biraz daha açar mısın?", "neutral", 10),
            ("Ne demek istediğini biraz daha anlatır mısın?", "neutral", 9),
        ],
        "followup_repair": [
            ("Tam anlayamadım, biraz daha açık söyler misin?", "neutral", 10),
            ("Ne demek istediğini kaçırdım, tekrar eder misin?", "neutral", 9),
        ],
    }

    for intent_name, rows in templates.items():
        for template_text, tone, priority in rows:
            _insert_template_if_missing(
                mm=mm,
                intent_name=intent_name,
                template_text=template_text,
                tone=tone,
                lang="tr",
                priority=priority,
            )

    print(">>> Templates seeded.")


def _insert_template_if_missing(
    mm: MemoryManager,
    intent_name: str,
    template_text: str,
    tone: str,
    lang: str,
    priority: int,
):
    existing = mm.get_all_templates(intent_name=intent_name, lang=lang)

    texts = {row["template_text"] for row in existing}
    if template_text in texts:
        return

    mm.add_template(
        intent_name=intent_name,
        template_text=template_text,
        tone=tone,
        lang=lang,
        priority=priority,
        is_active=1,
    )


def run_all():
    init_db()
    seed_profiles()
    seed_templates()


if __name__ == "__main__":
    run_all()
