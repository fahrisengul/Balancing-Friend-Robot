from memory.db import get_connection


class IntentRouter:
    def __init__(self):
        self.patterns = []
        self._load_patterns()

    def _load_patterns(self):
        with get_connection() as conn:
            rows = conn.execute("""
                SELECT intent_name, pattern_text
                FROM intent_patterns
            """).fetchall()

        self.patterns = [
            (r["intent_name"], r["pattern_text"].lower())
            for r in rows
        ]

        print(f">>> [INTENT ROUTER] {len(self.patterns)} pattern yüklendi.")

    def detect(self, text: str):
        if not text:
            return "fallback"

        text = text.lower()

        for intent, pattern in self.patterns:
            if pattern in text:
                return intent

        return "fallback"
