# memory/memory_writer.py

from datetime import datetime
from .embedder import Embedder
from .vector_index import VectorIndex


class MemoryWriter:
    def __init__(self, memory_manager):
        self.memory = memory_manager
        self.embedder = Embedder()
        self.index = VectorIndex()

    def process(self, text: str):
        text = (text or "").strip()
        if not text:
            return

        name = self._extract_name(text)
        if name:
            self._save_name(name)

        if self._is_meaningful(text):
            self._save_memory(text)

    def _extract_name(self, text):
        t = text.lower()

        if "bana " in t and " diyebilirsin" in t:
            start = t.find("bana ") + len("bana ")
            end = t.find(" diyebilirsin")
            if end > start:
                return text[start:end].strip().title()

        if "ben " in t and " tanem" in t:
            return "Tanem"

        return None

    def _save_name(self, name):
        try:
            self.memory.upsert_person_profile("tanem", name)
            print(f">>> [MEMORY NAME] {name}")
        except Exception as e:
            print(f">>> [MEMORY NAME ERROR] {e}")

    def _is_meaningful(self, text):
        if len(text.split()) < 3:
            return False

        t = text.lower()
        ignore = [
            "merhaba",
            "selam",
            "nasılsın",
            "tesekkür",
            "teşekkür",
            "görüşürüz",
        ]

        return not any(x in t for x in ignore)

    def _save_memory(self, text):
        try:
            vector = self.embedder.embed(text)

            memory_id = self.memory.add_episodic_memory(
                content=text,
                timestamp=datetime.utcnow().isoformat()
            )

            self.index.add(vector, memory_id)

        except Exception as e:
            print(f">>> [VECTOR SAVE ERROR] {e}")
