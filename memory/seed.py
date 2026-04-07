from .memory_manager import MemoryManager


def seed_templates():
    mm = MemoryManager()

    templates = [
        ("greeting", "Selam, ben Poodle.", 10),
        ("ask_name", "Benim adım Poodle.", 10),
        ("ask_identity", "Ben Poodle. Seninle konuşan robot arkadaşınım.", 10),
        ("ask_status", "İyiyim, teşekkür ederim. Sen nasılsın?", 10),
        ("thanks", "Rica ederim.", 10),
        ("acknowledge", "Tamam.", 5),
        ("clarify", "Seni tam anlayamadım. Bir kez daha söyler misin?", 10),
    ]

    for intent, text, priority in templates:
        mm.add_template(
            intent_name=intent,
            template_text=text,
            priority=priority
        )

    print(">>> Templates seeded.")


def seed_profiles():
    mm = MemoryManager()

    mm.ensure_default_tanem_profile()

    print(">>> Default profile seeded.")


def run_all():
    seed_profiles()
    seed_templates()


if __name__ == "__main__":
    run_all()
