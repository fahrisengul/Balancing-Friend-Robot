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

        # isim yakala
        name = self._extract_name(text)
        if name:
            self._save_name(name)

        # meaningful memory
        if self._is_meaningful(text):
            self._save_memory(text)

    # -----------------------
    def _save_memory(self, text):
        try:
            vector = self.embedder.embed(text)

            # DB insert → ID al
            memory_id = self.memory.add_episodic_memory(
                content=text,
                timestamp=datetime.utcnow().isoformat()
            )

            # vector index
            self.index.add(vector)

        except Exception as e:
            print(f">>> [VECTOR SAVE ERROR] {e}")

    # -----------------------
    def _extract_name(self, text):
        t = text.lower()

        if "bana " in t and " diyebilirsin" in t:
            start = t.find("bana ") + 5
            end = t.find(" diyebilirsin")

            return text[start:end].strip().title()

        return None

    def _save_name(self, name):
        if hasattr(self.memory, "upsert_person_profile"):
            self.memory.upsert_person_profile("tanem", name)

    def _is_meaningful(self, text):
        return len(text.split()) >= 3
