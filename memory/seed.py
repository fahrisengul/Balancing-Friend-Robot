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
            notes="Ana kullanıcı profili. Çocuk dostu, destekleyici, güvenli ve eğitim koçu tonunda konuşulmalı."
        )

    print(">>> Profiles seeded.")


def seed_intents():
    intent_definitions = [
        ("greeting", "social", "template", 100),
        ("farewell", "social", "template", 100),
        ("ask_name", "social", "template", 95),
        ("ask_identity", "social", "template", 95),
        ("ask_status", "social", "template", 95),
        ("thanks", "social", "template", 90),
        ("acknowledge", "social", "template", 80),

        ("conversation_start", "social", "template", 95),
        ("ask_question_back", "social", "template", 95),
        ("ask_topic", "social", "template", 92),
        ("open_topic", "social", "template", 92),
        ("ask_user_profile", "social", "llm", 90),
        ("share_preference", "social", "llm", 85),

        ("education_help", "education", "llm", 100),
        ("study_planning", "education", "llm", 98),
        ("homework_help", "education", "llm", 96),
        ("exam_anxiety", "education", "llm", 100),
        ("motivation_help", "education", "llm", 96),
        ("focus_help", "education", "llm", 95),
        ("request_advice", "education", "llm", 97),

        ("emotional_support", "emotion", "llm", 95),
        ("sadness_support", "emotion", "llm", 94),
        ("frustration_support", "emotion", "llm", 94),
        ("reassurance_request", "emotion", "llm", 92),

        ("question", "general", "llm", 70),
        ("statement", "general", "llm", 60),
        ("followup", "general", "template", 85),
        ("followup_repair", "general", "template", 85),

        ("ask_time", "utility", "skill", 100),
        ("ask_day_date", "utility", "skill", 100),
        ("ask_age", "utility", "skill", 100),
        ("ask_birthdate", "utility", "skill", 100),
        ("mute", "utility", "skill", 100),
        ("wake", "utility", "skill", 100),
    ]

    patterns = [
        ("greeting", "selam", "contains", "tr", 100),
        ("greeting", "merhaba", "contains", "tr", 100),
        ("greeting", "hey", "exact", "tr", 80),

        ("farewell", "gorusuruz", "contains", "tr", 100),
        ("farewell", "görüşürüz", "contains", "tr", 100),
        ("farewell", "hosca kal", "contains", "tr", 100),
        ("farewell", "hoşça kal", "contains", "tr", 100),

        ("ask_name", "adin ne", "contains", "tr", 100),
        ("ask_name", "adın ne", "contains", "tr", 100),

        ("ask_identity", "kimsin", "contains", "tr", 100),
        ("ask_identity", "kendini tanimlar misin", "contains", "tr", 100),
        ("ask_identity", "kendini tanımlar mısın", "contains", "tr", 100),

        ("ask_status", "nasilsin", "contains", "tr", 100),
        ("ask_status", "nasılsın", "contains", "tr", 100),
        ("ask_status", "her sey yolunda mi", "contains", "tr", 90),
        ("ask_status", "her şey yolunda mı", "contains", "tr", 90),
        ("ask_status", "iyi misin", "contains", "tr", 90),

        ("thanks", "tesekkur", "contains", "tr", 100),
        ("thanks", "teşekkür", "contains", "tr", 100),

        ("acknowledge", "tamam", "exact", "tr", 100),
        ("acknowledge", "peki", "exact", "tr", 95),
        ("acknowledge", "olur", "exact", "tr", 95),

        ("conversation_start", "beni tanimak ister misin", "contains", "tr", 100),
        ("conversation_start", "beni tanımak ister misin", "contains", "tr", 100),

        ("ask_question_back", "bana soru sor", "contains", "tr", 100),
        ("ask_question_back", "bana soru sorar misin", "contains", "tr", 100),
        ("ask_question_back", "bana soru sorar mısın", "contains", "tr", 100),
        ("ask_question_back", "beni tanimak icin soru sor", "contains", "tr", 95),
        ("ask_question_back", "beni tanımak için soru sor", "contains", "tr", 95),
        ("ask_question_back", "beni tanimak icin sorular sorar misin", "contains", "tr", 95),
        ("ask_question_back", "beni tanımak için sorular sorar mısın", "contains", "tr", 95),

        ("ask_topic", "ne konusalim", "contains", "tr", 100),
        ("ask_topic", "ne konuşalım", "contains", "tr", 100),

        ("open_topic", "bana bir konu ac", "contains", "tr", 100),
        ("open_topic", "bana bir konu aç", "contains", "tr", 100),
        ("open_topic", "konu ac", "contains", "tr", 95),
        ("open_topic", "konu aç", "contains", "tr", 95),
        ("open_topic", "hakkinda konusalim", "contains", "tr", 90),
        ("open_topic", "hakkında konuşalım", "contains", "tr", 90),

        ("ask_user_profile", "benimle ilgili ne biliyorsun", "contains", "tr", 100),
        ("ask_user_profile", "benim hakkimda ne biliyorsun", "contains", "tr", 100),
        ("ask_user_profile", "benim hakkımda ne biliyorsun", "contains", "tr", 100),

        ("education_help", "ders", "contains", "tr", 85),
        ("education_help", "matematik", "contains", "tr", 85),
        ("education_help", "fen", "contains", "tr", 80),
        ("education_help", "turkce", "contains", "tr", 80),
        ("education_help", "türkçe", "contains", "tr", 80),
        ("education_help", "ingilizce", "contains", "tr", 80),
        ("education_help", "ödev", "contains", "tr", 85),
        ("education_help", "odev", "contains", "tr", 85),

        ("study_planning", "ders calisma plani", "contains", "tr", 100),
        ("study_planning", "ders çalışma planı", "contains", "tr", 100),
        ("study_planning", "calisma plani yap", "contains", "tr", 95),
        ("study_planning", "çalışma planı yap", "contains", "tr", 95),

        ("homework_help", "odevime yardim eder misin", "contains", "tr", 100),
        ("homework_help", "ödevime yardım eder misin", "contains", "tr", 100),

        ("exam_anxiety", "sinav icin endiseliyim", "contains", "tr", 100),
        ("exam_anxiety", "sınav için endişeliyim", "contains", "tr", 100),
        ("exam_anxiety", "sinav stresi", "contains", "tr", 95),
        ("exam_anxiety", "sınav stresi", "contains", "tr", 95),
        ("exam_anxiety", "sinav beni geriyor", "contains", "tr", 95),
        ("exam_anxiety", "sınav beni geriyor", "contains", "tr", 95),

        ("motivation_help", "ders calismak istemiyorum", "contains", "tr", 100),
        ("motivation_help", "ders çalışmak istemiyorum", "contains", "tr", 100),
        ("motivation_help", "hic motivasyonum yok", "contains", "tr", 95),
        ("motivation_help", "hiç motivasyonum yok", "contains", "tr", 95),
        ("motivation_help", "calisamiyorum", "contains", "tr", 90),
        ("motivation_help", "çalışamıyorum", "contains", "tr", 90),

        ("focus_help", "odaklanamiyorum", "contains", "tr", 100),
        ("focus_help", "odaklanamıyorum", "contains", "tr", 100),
        ("focus_help", "dikkatim dagiliyor", "contains", "tr", 95),
        ("focus_help", "dikkatim dağılıyor", "contains", "tr", 95),

        ("request_advice", "ne onerirsin", "contains", "tr", 100),
        ("request_advice", "ne önerirsin", "contains", "tr", 100),
        ("request_advice", "ne yapmaliyim", "contains", "tr", 100),
        ("request_advice", "ne yapmalıyım", "contains", "tr", 100),
        ("request_advice", "yontem soyler misin", "contains", "tr", 95),
        ("request_advice", "yöntem söyler misin", "contains", "tr", 95),

        ("emotional_support", "uzgunum", "contains", "tr", 100),
        ("emotional_support", "üzgünüm", "contains", "tr", 100),
        ("emotional_support", "kendimi kotu hissediyorum", "contains", "tr", 100),
        ("emotional_support", "kendimi kötü hissediyorum", "contains", "tr", 100),

        ("sadness_support", "moralim bozuk", "contains", "tr", 100),
        ("sadness_support", "canim sikkın", "contains", "tr", 90),
        ("sadness_support", "canım sıkkın", "contains", "tr", 90),

        ("frustration_support", "sinirlendim", "contains", "tr", 100),
        ("frustration_support", "çok kızdım", "contains", "tr", 90),
        ("frustration_support", "buna cok sinir oldum", "contains", "tr", 90),
        ("frustration_support", "buna çok sinir oldum", "contains", "tr", 90),

        ("reassurance_request", "iyi olacak mi", "contains", "tr", 100),
        ("reassurance_request", "iyi olacak mı", "contains", "tr", 100),
        ("reassurance_request", "sence duzelir mi", "contains", "tr", 95),
        ("reassurance_request", "sence düzelir mi", "contains", "tr", 95),

        ("followup", "neden", "exact", "tr", 70),
        ("followup", "niye", "exact", "tr", 70),
        ("followup", "peki", "exact", "tr", 70),
        ("followup", "yani", "exact", "tr", 60),

        ("followup_repair", "ne demek istedin", "contains", "tr", 100),
        ("followup_repair", "bir daha soyler misin", "contains", "tr", 95),
        ("followup_repair", "bir daha söyler misin", "contains", "tr", 95),

        ("ask_time", "saat kac", "contains", "tr", 100),
        ("ask_time", "saat kaç", "contains", "tr", 100),

        ("ask_day_date", "bugun gunlerden ne", "contains", "tr", 100),
        ("ask_day_date", "bugün günlerden ne", "contains", "tr", 100),

        ("ask_age", "kac yasindayim", "contains", "tr", 100),
        ("ask_age", "kaç yaşındayım", "contains", "tr", 100),

        ("ask_birthdate", "dogum gunum ne zaman", "contains", "tr", 100),
        ("ask_birthdate", "doğum günüm ne zaman", "contains", "tr", 100),

        ("mute", "sus", "exact", "tr", 100),
        ("mute", "sessiz ol", "exact", "tr", 100),
        ("mute", "dur", "exact", "tr", 90),

        ("wake", "hey poodle", "contains", "tr", 100),
        ("wake", "hey puddle", "contains", "tr", 90),
        ("wake", "hey pudil", "contains", "tr", 90),
        ("wake", "poodle", "exact", "tr", 70),
    ]

    templates = {
        "greeting": [
            ("Selam.", "warm", 100),
            ("Merhaba.", "warm", 95),
            ("Buradayım.", "warm", 90),
        ],
        "farewell": [
            ("Görüşürüz.", "neutral", 100),
            ("Sonra konuşuruz.", "warm", 95),
            ("Kendine iyi bak.", "warm", 90),
        ],
        "ask_name": [
            ("Poodle.", "neutral", 100),
            ("Ben Poodle.", "neutral", 95),
        ],
        "ask_identity": [
            ("Poodle. Seninle konuşan robot arkadaşınım.", "warm", 100),
            ("Poodle. Sana eşlik eden sakin bir robotum.", "warm", 95),
        ],
        "ask_status": [
            ("İyiyim. Sen nasılsın?", "warm", 100),
            ("Fena değil. Sende durum nasıl?", "warm", 95),
            ("İdare eder. Sen nasılsın?", "warm", 90),
        ],
        "thanks": [
            ("Rica ederim.", "warm", 100),
            ("Ne demek.", "neutral", 95),
            ("Her zaman.", "warm", 90),
        ],
        "acknowledge": [
            ("Tamam.", "neutral", 100),
            ("Peki.", "neutral", 95),
        ],
        "followup": [
            ("Biraz daha anlatır mısın?", "neutral", 100),
            ("Orayı biraz açar mısın?", "neutral", 95),
        ],
        "followup_repair": [
            ("Tam anlayamadım. Bir daha söyler misin?", "neutral", 100),
            ("Bir kısmını kaçırdım. Tekrar eder misin?", "neutral", 95),
        ],

        "conversation_start": [
            ("Seni tanımak isterim. Neler yapmayı seversin?", "warm", 100),
            ("Biraz kendinden bahsetmek ister misin?", "warm", 95),
        ],
        "ask_question_back": [
            ("Sana bir şey sorayım: bugün nasıldı?", "warm", 100),
            ("Bir soru sorayım: en sevdiğin şey nedir?", "warm", 95),
        ],
        "ask_topic": [
            ("Oyunlar, okul ya da arkadaşlar... hangisi?", "warm", 100),
            ("Bir konu seçelim mi? Oyun, okul, arkadaşlar?", "warm", 95),
        ],
        "open_topic": [
            ("Bugün nasıl geçti?", "warm", 100),
            ("Okulda neler yaptın?", "warm", 95),
        ],

        "education_help": [
            ("Neresi zor geldi?", "coach", 100),
            ("İstersen birlikte plan yapalım.", "coach", 95),
            ("Küçük küçük ilerleyelim mi?", "coach", 90),
        ],
        "study_planning": [
            ("İstersen önce kısa bir plan yapalım.", "coach", 100),
            ("Bugün için küçük hedefler belirleyelim mi?", "coach", 95),
        ],
        "homework_help": [
            ("Tamam. Önce hangi dersten başlayalım?", "coach", 100),
            ("İstersen ödevi parçalara bölelim.", "coach", 95),
        ],
        "exam_anxiety": [
            ("Bu his çok normal. İstersen önce seni en çok geren kısmı bulalım.", "coach", 100),
            ("Sınav seni zorluyor gibi. Birlikte sakin bir plan yapabiliriz.", "coach", 95),
        ],
        "motivation_help": [
            ("İstersen çok küçük bir adımla başlayalım.", "coach", 100),
            ("Hadi önce sadece 10 dakikalık bir hedef koyalım.", "coach", 95),
        ],
        "focus_help": [
            ("Önce dikkatini dağıtan şeyi bulalım mı?", "coach", 100),
            ("İstersen kısa bir odak planı yapalım.", "coach", 95),
        ],
        "request_advice": [
            ("İstersen bunu adım adım düşünelim.", "coach", 100),
            ("Buna uygun birkaç öneri söyleyebilirim.", "coach", 95),
        ],
        "emotional_support": [
            ("Bu biraz zor hissettirmiş olabilir.", "warm", 100),
            ("İstersen anlatabilirsin. Dinliyorum.", "warm", 95),
        ],
        "sadness_support": [
            ("Moralinin bozulması anlaşılır bir şey.", "warm", 100),
            ("İstersen bunu birlikte konuşabiliriz.", "warm", 95),
        ],
        "frustration_support": [
            ("Buna sinirlenmen çok normal.", "warm", 100),
            ("İstersen önce sakinleşip sonra bakalım.", "warm", 95),
        ],
        "reassurance_request": [
            ("Bence düzelebilir. Adım adım gidersek daha kolay olur.", "warm", 100),
            ("Şu an zor gelse de toparlanabilir.", "warm", 95),
        ],
    }

    # Sprint 6: education follow-up bank
    followups = {
        "education_help": [
            ("İstersen önce en zor kısmı seçelim.", 100),
            ("Birlikte sade bir plan yapabiliriz.", 95),
            ("Hangi dersten başlamak istersin?", 90),
        ],
        "study_planning": [
            ("Bugün kaç dakika ayırabilirsin?", 100),
            ("Önce hangi dersi bitirmek istersin?", 95),
            ("Kısa bir plan mı, ayrıntılı plan mı istersin?", 90),
        ],
        "homework_help": [
            ("Önce hangi ödev daha kısa?", 100),
            ("İstersen ilk sorudan başlayalım.", 95),
            ("Seni en çok zorlayan yer hangisi?", 90),
        ],
        "exam_anxiety": [
            ("Şu an seni en çok ne geriyor?", 100),
            ("Önce bunu küçük parçalara bölelim mi?", 95),
            ("En zor gelen ders hangisi?", 90),
        ],
        "motivation_help": [
            ("Sadece 5 dakikalık bir başlangıç yapalım mı?", 100),
            ("En kolay yerden başlamak ister misin?", 95),
            ("Önce küçük bir hedef seçelim mi?", 90),
        ],
        "focus_help": [
            ("Dikkatini en çok ne dağıtıyor?", 100),
            ("Önce 10 dakikalık sessiz çalışma deneyelim mi?", 95),
            ("Telefonu biraz uzağa koymak ister misin?", 90),
        ],
        "request_advice": [
            ("İstersen bunu birlikte adım adım düşünelim.", 100),
            ("Önce en yakın problemi seçelim mi?", 95),
        ],
        "emotional_support": [
            ("İstersen önce ne olduğunu anlat.", 100),
        ],
        "sadness_support": [
            ("Bugün seni en çok üzen şey neydi?", 100),
        ],
        "frustration_support": [
            ("Bunu yapan şey neydi?", 100),
        ],
        "reassurance_request": [
            ("İstersen birlikte nasıl düzelebileceğine bakalım.", 100),
        ],
        "conversation_start": [
            ("En sevdiğin oyun nedir?", 100),
            ("Okulda en çok hangi dersi seviyorsun?", 95),
        ],
        "ask_question_back": [
            ("Bugün seni en çok ne mutlu etti?", 100),
            ("Şu sıralar en çok neyle ilgileniyorsun?", 95),
        ],
        "ask_topic": [
            ("İstersen önce sevdiğin şeylerden başlayalım.", 100),
        ],
        "open_topic": [
            ("İstersen detayını anlat.", 100),
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
