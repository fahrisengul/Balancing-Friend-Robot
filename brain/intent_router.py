import re
from typing import Optional, Tuple


class IntentRouter:
    def __init__(self):
        self.patterns = []

    def load_patterns(self, patterns):
        self.patterns = [
            (p["intent_name"], re.compile(p["pattern"], re.IGNORECASE))
            for p in patterns
        ]
        print(f">>> [INTENT ROUTER] {len(self.patterns)} pattern yüklendi.")

    def detect(self, text: str) -> Tuple[str, float]:
        if not text:
            return "fallback", 0.0

        for intent_name, pattern in self.patterns:
            if pattern.search(text):
                return intent_name, 0.9

        return "fallback", 0.3
