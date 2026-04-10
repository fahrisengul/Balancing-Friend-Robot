import random


class PolicyDecision:
    def __init__(self, source: str, clarify_text: str = None):
        self.source = source  # "template" | "skill" | "llm" | "clarify"
        self.clarify_text = clarify_text


class ResponsePolicy:
    def __init__(self):
        self.last_reply = None

    # -------------------------------------------------
    # SOURCE SELECTION
    # -------------------------------------------------
    def choose_source(self, text: str, intent: str) -> PolicyDecision:
        t = (text or "").lower().strip()

        # -----------------------------------
        # 1. CRITICAL: boş / anlamsız giriş
        # -----------------------------------
        if not t or len(t) < 2:
            return PolicyDecision(
                "clarify",
                "Biraz daha açık söyler misin?"
            )

        # -----------------------------------
        # 2. SOCIAL / FAST PATH (template)
        # -----------------------------------
        if intent in {
            "greeting",
            "farewell",
            "ask_name",
            "ask_identity",
            "ask_status",
            "thanks",
            "acknowledge",
            "conversation_start",
            "ask_question_back",
            "ask_topic",
            "open_topic",
        }:
            return PolicyDecision("template")

        # -----------------------------------
        # 3. EDUCATION / SKILL
        # -----------------------------------
        if intent in {
            "exam_anxiety",
            "request_advice",
        }:
            return PolicyDecision("skill")

        # -----------------------------------
        # 4. CONFUSION / REPAIR
        # -----------------------------------
        if intent in {
            "clarification_needed",
            "followup_repair",
        }:
            return PolicyDecision(
                "clarify",
                self._repair_phrase()
            )

        # -----------------------------------
        # 5. DEFAULT → LLM
        # -----------------------------------
        return PolicyDecision("llm")

    # -------------------------------------------------
    # FINAL RESPONSE POST-PROCESS
    # -------------------------------------------------
    def apply(self, raw: str) -> str:
        if not raw:
            return self._repair_phrase()

        text = raw.strip()

        # -----------------------------------
        # 1. LENGTH CONTROL (çok uzunsa kes)
        # -----------------------------------
        sentences = self._split_sentences(text)

        if len(sentences) > 3:
            sentences = sentences[:3]

        text = " ".join(sentences).strip()

        # -----------------------------------
        # 2. REPETITION GUARD
        # -----------------------------------
        if self.last_reply and self._is_similar(text, self.last_reply):
            text = self._diversify(text)

        self.last_reply = text

        return text

    # -------------------------------------------------
    # CHILD-SAFE PHRASES
    # -------------------------------------------------
    def _repair_phrase(self):
        return random.choice([
            "Tam anlayamadım. Biraz daha açık söyler misin?",
            "Bunu biraz daha net anlatabilir misin?",
            "Biraz daha açarsan daha iyi yardımcı olabilirim."
        ])

    def _diversify(self, text):
        return random.choice([
            "Bunu farklı bir şekilde söyleyeyim.",
            "Şöyle düşünebiliriz.",
            "Başka bir açıdan bakalım."
        ])

    # -------------------------------------------------
    # HELPERS
    # -------------------------------------------------
    def _split_sentences(self, text):
        parts = []
        current = ""

        for ch in text:
            current += ch
            if ch in ".!?":
                parts.append(current.strip())
                current = ""

        if current:
            parts.append(current.strip())

        return parts

    def _is_similar(self, a: str, b: str) -> bool:
        a = a.lower()
        b = b.lower()

        if a == b:
            return True

        # basit similarity
        common = set(a.split()) & set(b.split())
        ratio = len(common) / max(len(a.split()), 1)

        return ratio > 0.7
