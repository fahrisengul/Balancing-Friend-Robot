import re
from typing import Optional


class EducationEngine:
    """
    Sprint 6 - Education Engine v2

    Hedef:
    - 12-14 yaş için sade, güvenli ve uygulanabilir eğitim koçluğu
    - kısa cevap
    - önce duyguyu kabul et, sonra küçük aksiyon ver
    - mümkün olduğunca deterministik davran
    """

    def __init__(self):
        self.default_step_minutes = 10
        self.short_step_minutes = 5

    # -------------------------------------------------
    # PUBLIC ENTRY
    # -------------------------------------------------
    def handle(self, text: str, intent: str) -> Optional[str]:
        normalized = self._normalize(text)

        if not normalized:
            return None

        # Education / coaching intents
        if intent == "exam_anxiety":
            return self._handle_exam_anxiety(normalized)

        if intent == "request_advice":
            return self._handle_request_advice(normalized)

        if intent == "study_planning":
            return self._handle_study_planning(normalized)

        if intent == "homework_help":
            return self._handle_homework_help(normalized)

        if intent == "motivation_help":
            return self._handle_motivation_help(normalized)

        if intent == "focus_help":
            return self._handle_focus_help(normalized)

        if intent == "education_help":
            return self._handle_general_education_help(normalized)

        # Emotion intents that still benefit from coaching-safe structure
        if intent == "emotional_support":
            return self._handle_emotional_support(normalized)

        if intent == "sadness_support":
            return self._handle_sadness_support(normalized)

        if intent == "frustration_support":
            return self._handle_frustration_support(normalized)

        if intent == "reassurance_request":
            return self._handle_reassurance_request(normalized)

        # Mixed / broad user turns
        if self._looks_like_bad_exam_reflection(normalized):
            return self._handle_bad_exam_reflection(normalized)

        if self._looks_like_study_resistance(normalized):
            return self._handle_motivation_help(normalized)

        if self._looks_like_focus_problem(normalized):
            return self._handle_focus_help(normalized)

        return None

    # -------------------------------------------------
    # CORE EDUCATION HANDLERS
    # -------------------------------------------------
    def _handle_exam_anxiety(self, text: str) -> str:
        if self._asks_for_count(text, 5):
            return (
                "1. Derin nefes al.\n"
                "2. En kolay yerden başla.\n"
                "3. Zor soruda hemen takılma.\n"
                "4. Kendine küçük hedef koy.\n"
                "5. Kendine sert davranma."
            )

        if self._asks_for_count(text, 3):
            return (
                "1. Derin nefes al.\n"
                "2. En kolay yerden başla.\n"
                "3. Sadece küçük bir hedefe odaklan."
            )

        return (
            "Bu his normal. Önce sakinleşelim, sonra seni en çok geren kısmı seçelim."
        )

    def _handle_request_advice(self, text: str) -> str:
        if self._asks_for_count(text, 5):
            return (
                "1. İşini küçük parçalara böl.\n"
                "2. Önce kolay kısmı yap.\n"
                "3. Kısa mola ver.\n"
                "4. Tek seferde her şeyi bitirmeye çalışma.\n"
                "5. Bitirdiğinde kendini takdir et."
            )

        if self._asks_for_count(text, 3):
            return (
                "1. Küçük bir yerden başla.\n"
                "2. Kısa süre çalış.\n"
                "3. Sonra kısa mola ver."
            )

        if "sinav" in text or "sınav" in text:
            return (
                "Önce kısa bir tekrar yap. Sonra "
                f"{self.default_step_minutes} dakika soru çözmeyi dene."
            )

        if "ders" in text or "calisma" in text or "çalışma" in text:
            return (
                f"Önce {self.default_step_minutes} dakikalık küçük bir hedef seç. "
                "Sonra kısa mola ver."
            )

        return "İstersen önce en zor gelen kısmı seçelim. Sonra küçük bir plan yaparız."

    def _handle_study_planning(self, text: str) -> str:
        subject = self._detect_subject(text)
        if subject:
            return (
                f"Önce {subject} için {self.default_step_minutes} dakikalık bir hedef koyalım. "
                "Sonra 5 dakika mola verelim."
            )

        return (
            f"Önce {self.default_step_minutes} dakikalık bir hedef seç. "
            "Sonra 5 dakika mola ver. İstersen bunu derse göre bölebiliriz."
        )

    def _handle_homework_help(self, text: str) -> str:
        subject = self._detect_subject(text)
        if subject:
            return f"Tamam. Önce {subject} ödevinin en kısa kısmını bitirelim."

        return "Ödevi parçalara bölelim. Önce en kısa kısmı bitirelim."

    def _handle_motivation_help(self, text: str) -> str:
        return (
            f"Büyük başlamayalım. Sadece {self.short_step_minutes} dakika denemek ister misin?"
        )

    def _handle_focus_help(self, text: str) -> str:
        return (
            "Önce dikkatini dağıtan şeyi kapat. Sonra sadece bir konuya "
            f"{self.default_step_minutes} dakika odaklan."
        )

    def _handle_general_education_help(self, text: str) -> str:
        subject = self._detect_subject(text)

        if subject == "matematik":
            return "Matematikte önce en kolay sorudan başlamak iyi gelir."

        if subject == "turkce":
            return "Türkçede önce kısa parçayı okuyup ana fikri bulmayı deneyebilirsin."

        if subject == "ingilizce":
            return "İngilizcede önce kısa tekrar yapmak işini kolaylaştırabilir."

        if "odev" in text or "ödev" in text:
            return "İstersen ödevi küçük adımlara bölelim."

        if "calisma" in text or "çalışma" in text:
            return "Kısa süreyle başlayıp sonra mola vermek daha kolay olur."

        return "İstersen bunu küçük adımlara bölelim. Böylece daha kolay olur."

    # -------------------------------------------------
    # EMOTIONAL SUPPORT WITH COACHING SHAPE
    # -------------------------------------------------
    def _handle_emotional_support(self, text: str) -> str:
        return "Bu biraz zor hissettirmiş olabilir. İstersen önce ne olduğunu anlat."

    def _handle_sadness_support(self, text: str) -> str:
        return "Moralinin bozulması anlaşılır bir şey. İstersen en çok neyin üzdüğünü söyle."

    def _handle_frustration_support(self, text: str) -> str:
        return "Buna sinirlenmen normal. İstersen önce sakinleşip sonra bakalım."

    def _handle_reassurance_request(self, text: str) -> str:
        return "Bence düzelebilir. Adım adım gidersek daha kolay olur."

    # -------------------------------------------------
    # MIXED / MULTI-TURN COACHING
    # -------------------------------------------------
    def _handle_bad_exam_reflection(self, text: str) -> str:
        return (
            "Bu can sıkıcı olabilir. Önce nerede zorlandığını bulalım, "
            "sonra bir sonraki adımı seçelim."
        )

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
        if str(n) in tokens:
            return True

        turkish_numbers = {
            2: {"iki"},
            3: {"uc", "üç"},
            4: {"dort", "dört"},
            5: {"bes", "beş"},
        }
        return n in turkish_numbers and any(tok in tokens for tok in turkish_numbers[n])

    def _detect_subject(self, text: str) -> Optional[str]:
        if "matematik" in text:
            return "matematik"
        if "turkce" in text or "türkçe" in text:
            return "turkce"
        if "ingilizce" in text:
            return "ingilizce"
        if "fen" in text:
            return "fen"
        return None

    def _looks_like_bad_exam_reflection(self, text: str) -> bool:
        return (
            ("sinavim vardi" in text or "sınavım vardı" in text or "sinav" in text or "sınav" in text)
            and (
                "iyi gecmedi" in text
                or "iyi geçmedi" in text
                or "neden boyle" in text
                or "neden böyle" in text
                or "ne yapmaliyim" in text
                or "ne yapmalıyım" in text
            )
        )

    def _looks_like_study_resistance(self, text: str) -> bool:
        patterns = [
            "ders calismak istemiyorum",
            "ders çalışmak istemiyorum",
            "hic motivasyonum yok",
            "hiç motivasyonum yok",
            "calisamiyorum",
            "çalışamıyorum",
        ]
        return any(p in text for p in patterns)

    def _looks_like_focus_problem(self, text: str) -> bool:
        patterns = [
            "odaklanamiyorum",
            "odaklanamıyorum",
            "dikkatim dagiliyor",
            "dikkatim dağılıyor",
        ]
        return any(p in text for p in patterns)
