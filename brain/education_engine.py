import re
from typing import Optional


class EducationEngine:
    """
    Sprint 6 - Education Engine
    12-14 yaş için kısa, sade, güvenli eğitim koçu motoru.

    Öncelikler:
    - kaygıyı azaltmak
    - küçük adımla başlatmak
    - net ve uygulanabilir öneri vermek
    - uzun ve soyut konuşmamak
    """

    def handle(self, text: str, intent: str) -> Optional[str]:
        normalized = self._normalize(text)

        if intent == "exam_anxiety":
            return self._handle_exam_anxiety(normalized)

        if intent == "request_advice":
            return self._handle_request_advice(normalized)

        if intent == "study_planning":
            return self._handle_study_planning(normalized)

        if intent == "motivation_help":
            return self._handle_motivation_help(normalized)

        if intent == "focus_help":
            return self._handle_focus_help(normalized)

        if intent == "homework_help":
            return self._handle_homework_help(normalized)

        if intent == "education_help":
            return self._handle_general_education_help(normalized)

        if intent == "emotional_support":
            return self._handle_emotional_support(normalized)

        if intent == "sadness_support":
            return self._handle_sadness_support(normalized)

        if intent == "frustration_support":
            return self._handle_frustration_support(normalized)

        if intent == "reassurance_request":
            return self._handle_reassurance_request(normalized)

        return None

    # -------------------------------------------------
    # EDUCATION
    # -------------------------------------------------
    def _handle_exam_anxiety(self, text: str) -> str:
        if self._asks_for_count(text, 5):
            return (
                "1. Derin nefes al.\n"
                "2. En kolay sorudan başla.\n"
                "3. Zor soruda çok oyalanma.\n"
                "4. Kendine küçük hedef koy.\n"
                "5. Kendine sert davranma."
            )

        return "Bu his normal. İstersen önce seni en çok geren kısmı bulalım."

    def _handle_request_advice(self, text: str) -> str:
        if self._asks_for_count(text, 5):
            return (
                "1. Yapacağın işi küçük parçalara böl.\n"
                "2. Önce kolay kısmı bitir.\n"
                "3. Kısa mola ver.\n"
                "4. Tek seferde her şeyi çözmeye çalışma.\n"
                "5. Bittiğinde kendini takdir et."
            )

        if "sinav" in text or "sınav" in text:
            return "Önce kısa bir tekrar yap. Sonra 10 dakikalık soru çözümü dene."

        if "ders" in text:
            return "Önce 10 dakikalık küçük bir hedef koy. Sonra kısa mola ver."

        return "İstersen önce en zor gelen kısmı seçelim. Sonra küçük bir plan yaparız."

    def _handle_study_planning(self, text: str) -> str:
        return (
            "Önce 10 dakikalık bir hedef seç. Sonra 5 dakika mola ver. "
            "İstersen bunu derse göre birlikte bölebiliriz."
        )

    def _handle_motivation_help(self, text: str) -> str:
        return "Büyük başlamayalım. Sadece 5 dakika denemek ister misin?"

    def _handle_focus_help(self, text: str) -> str:
        return "Önce dikkatini dağıtan şeyi kapat. Sonra sadece bir konuya 10 dakika odaklan."

    def _handle_homework_help(self, text: str) -> str:
        return "Ödevi parçalara bölelim. Önce en kısa kısmı bitirelim."

    def _handle_general_education_help(self, text: str) -> str:
        if "matematik" in text:
            return "Matematikte önce en kolay sorudan başlamak iyi gelir."

        if "odev" in text or "ödev" in text:
            return "İstersen ödevi küçük adımlara bölelim."

        if "calisma" in text or "çalışma" in text:
            return "Kısa süreyle başlayıp sonra mola vermek daha kolay olur."

        return "İstersen bunu küçük adımlara bölelim. Böylece daha kolay olur."

    # -------------------------------------------------
    # EMOTION
    # -------------------------------------------------
    def _handle_emotional_support(self, text: str) -> str:
        return "Bu biraz zor hissettirmiş olabilir. İstersen anlatabilirsin, dinliyorum."

    def _handle_sadness_support(self, text: str) -> str:
        return "Moralinin bozulması anlaşılır bir şey. İstersen ne olduğunu anlat."

    def _handle_frustration_support(self, text: str) -> str:
        return "Buna sinirlenmen normal. İstersen önce sakinleşip sonra bakalım."

    def _handle_reassurance_request(self, text: str) -> str:
        return "Bence düzelebilir. Adım adım gidersek daha kolay olur."

    # -------------------------------------------------
    # HELPERS
    # -------------------------------------------------
    def _normalize(self, text: str) -> str:
        t = (text or "").lower().strip()
        t = (
            t.replace("ı", "i")
            .replace("ğ", "g")
            .replace("ş", "s")
            .replace("ç", "c")
            .replace("ö", "o")
            .replace("ü", "u")
        )
        t = re.sub(r"\s+", " ", t)
        return t

    def _asks_for_count(self, text: str, n: int) -> bool:
        tokens = set(text.split())

        digit_match = str(n) in tokens

        turkish_numbers = {
            2: {"iki"},
            3: {"uc", "üç"},
            4: {"dort", "dört"},
            5: {"bes", "beş"},
        }

        word_match = n in turkish_numbers and any(tok in tokens for tok in turkish_numbers[n])
        return digit_match or word_match
