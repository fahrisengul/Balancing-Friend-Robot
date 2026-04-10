from memory.db import get_connection


class IntentRouter:
    def __init__(self):
        self.patterns = []
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

        self.patterns = [
            {
                "intent_name": row["intent_name"],
                "pattern_text": (row["pattern_text"] or "").lower().strip(),
                "match_type": (row["match_type"] or "contains").lower().strip(),
                "priority": row["priority"] or 0,
            }
            for row in rows
        ]

        print(f">>> [INTENT ROUTER] {len(self.patterns)} pattern yüklendi.")

    def reload(self):
        self._load_patterns()

    def detect(self, text: str) -> str:
        cleaned = (text or "").strip()
        if not cleaned:
            return "clarification_needed"

        normalized = self._normalize(cleaned)

        for rule in self.patterns:
            intent_name = rule["intent_name"]
            pattern_text = rule["pattern_text"]
            match_type = rule["match_type"]

            if not pattern_text:
                continue

            if match_type == "exact":
                if normalized == pattern_text:
                    return intent_name

            elif match_type == "starts_with":
                if normalized.startswith(pattern_text):
                    return intent_name

            else:
                # default: contains
                if pattern_text in normalized:
                    return intent_name

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
        return " ".join(t.split())
