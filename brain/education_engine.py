import re
from typing import Optional


class EducationEngine:
    """
    12-14 yaş için sade, kısa ve güvenli eğitim koçu motoru.
    Amaç:
    - kaygıyı düzenlemek
    - küçük adım önermek
    - net ve kısa cevap vermek
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
            return self._handle_motivation(normalized)

        if intent == "focus_help":
            return self._handle_focus(normalized)

        if intent == "homework_help":
            return self._handle_homework(normalized)

        if intent == "education_help":
            return self._handle_general_education(normalized)

        return None

    # -------------------------------------------------
    # HANDLERS
    # -------------------------------------------------
    def _handle_exam_anxiety(self, text: str) -> str:
        if self._asks_for_count(text, 5):
            return (
                "1. Derin nefes al.\n"
                "2. En kolay yerden başla.\n"
                "3. Kendine kısa bir hedef koy.\n"
                "4. Zor soruda hemen takılı kalma.\n"
                "5. Kendine sert davranma."
            )

        return (
            "Bu his normal. Önce sakinleşelim, sonra en zor gelen kısmı birlikte seçelim."
        )

    def _handle_request_advice(self, text: str) -> str:
        if self._asks_for_count(text, 5):
            return (
                "1. İşini küçük parçalara böl.\n"
                "2. Önce kolay kısmı bitir.\n"
                "3. Kısa mola ver.\n"
                "4. Tek seferde her şeyi çözmeye çalışma.\n"
                "5. Bittiğinde kendini takdir et."
            )

        if "sinav" in text or "sınav" in text:
            return "Önce kısa tekrar yap. Sonra 10 dakika soru çözmeyi dene."

        if "ders" in text:
            return "Önce 10 dakikalık küçük bir hedef seç. Sonra kısa mola ver."

        return "İstersen önce en zor gelen kısmı seçelim. Sonra küçük bir plan yaparız."

    def _handle_study_planning(self, text: str) -> str:
        return (
            "Önce 10 dakikalık bir hedef seç. Sonra 5 dakika mola ver. "
            "İstersen bunu birlikte derse göre de bölebiliriz."
        )

    def _handle_motivation(self, text: str) -> str:
        return (
            "Tamam. Büyük başlamayalım. Sadece 5 dakika denemek ister misin?"
        )

    def _handle_focus(self, text: str) -> str:
        return (
            "Önce dikkatini dağıtan şeyi kapat. Sonra sadece bir konuya 10 dakika odaklan."
        )

    def _handle_homework(self, text: str) -> str:
        return (
            "Ödevi parçalara bölelim. Önce en kısa kısmı bitirelim."
        )

    def _handle_general_education(self, text: str) -> str:
        if "matematik" in text:
            return "Matematikte önce en kolay sorudan başlamak iyi gelir."

        if "odev" in text or "ödev" in text:
            return "İstersen ödevi küçük adımlara bölelim."

        if "calisma" in text or "çalışma" in text:
            return "Kısa süreyle başlayıp sonra mola vermek daha kolay olur."

        return "İstersen bunu küçük adımlara bölelim. Böylece daha kolay olur."

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
        number_tokens = {str(n)}
        turkish_numbers = {
            2: {"iki"},
            3: {"uc", "üç"},
            4: {"dort", "dört"},
            5: {"bes", "beş"},
        }

        tokens = set(text.split())
        if any(tok in tokens for tok in number_tokens):
            return True

        if n in turkish_numbers and any(tok in tokens for tok in turkish_numbers[n]):
            return True

        return False
