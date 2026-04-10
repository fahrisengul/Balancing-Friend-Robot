import re
from typing import Dict, List, Optional

from memory.db import get_connection


class IntentRouter:
    def __init__(self):
        self.patterns: List[Dict] = []
        self._load_patterns()

    def _load_patterns(self):
        with get_connection() as conn:
            rows = conn.execute(
                """
                SELECT intent_name, pattern_text, match_type, priority
                FROM intent_patterns
                ORDER BY priority DESC, id ASC
                """
            ).fetchall()

        self.patterns = []
        for row in rows:
            pattern_text = (row["pattern_text"] or "").strip()
            if not pattern_text:
                continue

            self.patterns.append(
                {
                    "intent_name": row["intent_name"],
                    "pattern_text": pattern_text,
                    "match_type": (row["match_type"] or "contains").strip().lower(),
                    "priority": row["priority"] or 0,
                }
            )

        print(f">>> [INTENT ROUTER] {len(self.patterns)} pattern yüklendi.")

    def reload(self):
        self._load_patterns()

    def detect(self, text: str, context: Optional[dict] = None) -> str:
        cleaned = (text or "").strip()
        normalized = self._normalize(cleaned)
        context = context or {}

        if not normalized:
            return "clarification_needed"

        # -----------------------------------
        # Kısa follow-up taşıma
        # -----------------------------------
        short_followups = {
            "neden",
            "niye",
            "nasil",
            "nasıl",
            "peki",
            "yani",
            "sonra",
        }
        if normalized in short_followups and context.get("current_topic"):
            return "followup"

        # -----------------------------------
        # Kod kontrollü yüksek değerli sosyal intentler
        # -----------------------------------
        if self._contains_any(
            normalized,
            [
                "beni tanimak ister misin",
                "beni tanımak ister misin",
                "beni tanir misin",
                "beni tanır mısın",
            ],
        ):
            return "conversation_start"

        if self._contains_any(
            normalized,
            [
                "bana soru sor",
                "bana soru sorar misin",
                "bana soru sorar mısın",
                "beni tanimak icin soru sor",
                "beni tanımak için soru sor",
                "beni tanimak icin sorular sorar misin",
                "beni tanımak için sorular sorar mısın",
            ],
        ):
            return "ask_question_back"

        if self._contains_any(
            normalized,
            [
                "ne konusalim",
                "ne konuşalım",
                "hangi konuyu konusalim",
                "hangi konuyu konuşalım",
            ],
        ):
            return "ask_topic"

        if self._contains_any(
            normalized,
            [
                "bana bir konu ac",
                "bana bir konu aç",
                "konu ac",
                "konu aç",
            ],
        ):
            return "open_topic"

        # -----------------------------------
        # Daha doğal status / relation yorumları
        # -----------------------------------
        if self._contains_any(
            normalized,
            [
                "her sey yolunda mi",
                "her şey yolunda mı",
                "iyi misin",
                "durum nasil",
                "durum nasıl",
            ],
        ):
            return "ask_status"

        if self._contains_any(
            normalized,
            [
                "neler biliyorsun",
                "benimle ilgili ne biliyorsun",
                "benim hakkimda ne biliyorsun",
                "benim hakkımda ne biliyorsun",
            ],
        ):
            return "ask_user_profile"

        # -----------------------------------
        # Eğitim / tavsiye / endişe
        # -----------------------------------
        if self._contains_any(
            normalized,
            [
                "sinav icin endiseliyim",
                "sınav için endişeliyim",
                "sinav stresi",
                "sınav stresi",
                "endiseliyim",
                "endişeliyim",
                "kaygiliyim",
                "kaygılıyım",
            ],
        ):
            return "exam_anxiety"

        if self._contains_any(
            normalized,
            [
                "ne onerirsin",
                "ne önerirsin",
                "yontem soyler misin",
                "yöntem söyler misin",
                "ne yapmaliyim",
                "ne yapmalıyım",
            ],
        ):
            return "request_advice"

        # -----------------------------------
        # DB-backed pattern matching
        # -----------------------------------
        for rule in self.patterns:
            intent_name = rule["intent_name"]
            pattern_text = rule["pattern_text"]
            match_type = rule["match_type"]

            pattern_norm = self._normalize(pattern_text)

            if match_type == "exact":
                if normalized == pattern_norm:
                    return intent_name

            elif match_type == "starts_with":
                if normalized.startswith(pattern_norm):
                    return intent_name

            else:
                if pattern_norm in normalized:
                    return intent_name

        # -----------------------------------
        # Genel soru fallback
        # -----------------------------------
        if "?" in cleaned:
            return "question"

        question_words = {
            "ne",
            "neden",
            "niye",
            "nasil",
            "nasıl",
            "hangi",
            "kim",
            "kac",
            "kaç",
            "nerede",
            "mi",
            "mı",
            "mu",
            "mü",
        }

        tokens = normalized.split()
        if any(tok in question_words for tok in tokens):
            return "question"

        if len(tokens) > 0:
            return "statement"

        return "general"

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

    def _contains_any(self, text: str, patterns: List[str]) -> bool:
        return any(self._normalize(p) in text for p in patterns)
