from typing import Optional, Set


class IntentRouter:
    @staticmethod
    def normalize(text: str) -> str:
        t = (text or "").strip().lower()
        return (
            t.replace("ı", "i")
             .replace("ğ", "g")
             .replace("ş", "s")
             .replace("ç", "c")
             .replace("ö", "o")
             .replace("ü", "u")
        )

    @classmethod
    def detect_intent(cls, text: str) -> str:
        t = cls.normalize(text)
        raw = (text or "").lower()

        if "merhaba" in t or "selam" in t or "merhabalar" in t or raw.startswith("hey "):
            if "nasilsin" in t:
                return "ask_status"
            return "greeting"

        if "nasilsin" in t or "iyi misin" in t:
            return "ask_status"

        if "tesekkur" in t or "sağol" in raw or "sagol" in t:
            return "thanks"

        if "gorusuruz" in t or "hosca kal" in t:
            return "farewell"

        if "adın ne" in raw or "senin adin ne" in t or "senin adın ne" in raw:
            return "ask_name"

        if "kendini tanimlar misin" in t or "kendini tanımlar mısın" in raw or "kimsin" in t:
            return "ask_identity"

        if "bana " in t and " diyebilirsin" in t:
            return "user_name_define"

        if "benim adim nedir" in t or "benim adım nedir" in raw:
            return "ask_user_name"

        if "beni duyabiliyor musun" in raw or "beni duyabiliyormusun" in raw or "sesim geliyor mu" in raw:
            return "audio_check"

        if ("lgs" in t or "dgs" in t) and ("konu" in t or "list" in t or "odaklan" in t):
            return "education_topics"

        if (
            "sinav stresi" in t
            or "sınav stresi" in raw
            or "ozet verir misin" in t
            or "özet verir misin" in raw
            or "nasil calismaliyim" in t
            or "nasıl çalışmalıyım" in raw
            or "strateji" in t
            or "taktik" in t
            or ("lgs" in t and "bilgi" in t)
        ):
            return "exam_support"

        if (
            "nedir" in t
            or "anlatir misin" in t
            or "anlatır mısın" in raw
            or "detay verir misin" in raw
            or "bilgi verir misin" in raw
        ):
            return "concept_explanation"

        if "konusalim" in t or "konuşalım" in raw:
            return "conversation_start"

        return "general"

    @classmethod
    def detect_mode(cls, text: str, intent: str) -> str:
        t = cls.normalize(text)

        if intent in {"education_topics", "exam_support", "concept_explanation"}:
            return "education"

        education_tokens: Set[str] = {
            "lgs", "dgs", "sinav", "ders", "matematik", "turkce",
            "inkilap", "fen", "ingilizce", "din", "konu", "ozet",
            "sayi", "cebir", "geometri", "karekok", "uslu",
        }

        if any(tok in t for tok in education_tokens):
            return "education"

        return "general"

    @classmethod
    def should_clarify(cls, text: str, intent: str) -> bool:
        if intent in {
            "greeting", "ask_status", "thanks", "ask_name",
            "ask_identity", "audio_check", "user_name_define",
            "ask_user_name", "education_topics", "exam_support",
            "concept_explanation", "conversation_start",
        }:
            return False

        t = cls.normalize(text)

        if len(t.split()) <= 1:
            return True

        bad_fragments = ["in club", "now see", "sinov sinov", "3 stres"]
        if any(x in t for x in bad_fragments):
            return True

        return False

    @staticmethod
    def intent_guard(text: str, intent: str) -> Optional[str]:
        if intent == "greeting":
            return "Selam!"

        if intent == "ask_status":
            return "İyiyim. Sen nasılsın?"

        if intent == "thanks":
            return "Rica ederim."

        if intent == "farewell":
            return "Görüşürüz."

        if intent == "ask_name":
            return "Ben Poodle."

        if intent == "ask_identity":
            return "Ben Poodle. Seninle konuşan robot arkadaşınım."

        if intent == "audio_check":
            return "Evet, seni duyuyorum."

        if intent == "conversation_start":
            return "Tamam. Ne hakkında konuşalım?"

        return None
