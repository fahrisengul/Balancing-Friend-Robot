# memory/memory_writer.py

import time
import re


class MemoryWriter:
    def __init__(self, memory_manager):
        self.mm = memory_manager

    # -----------------------------
    # MAIN ENTRY
    # -----------------------------
    def process(self, text: str):
        text = text.lower().strip()

        if not text or len(text) < 3:
            return

        self._extract_preferences(text)
        self._extract_difficulties(text)
        self._extract_events(text)

    # -----------------------------
    # PREFERENCE EXTRACTION
    # -----------------------------
    def _extract_preferences(self, text):
        patterns = [
            r"en sevdiğim (.*)",
            r"(.*) seviyorum",
            r"(.*) hoşuma gidiyor"
        ]

        for p in patterns:
            match = re.search(p, text)
            if match:
                value = match.group(1).strip()
                self._save_profile("likes", value)
                return

    # -----------------------------
    # DIFFICULTY EXTRACTION
    # -----------------------------
    def _extract_difficulties(self, text):
        patterns = [
            r"(.*) zor geliyor",
            r"(.*) anlamıyorum",
            r"(.*) yapamıyorum",
            r"(.*) zorlanıyorum"
        ]

        for p in patterns:
            match = re.search(p, text)
            if match:
                value = match.group(1).strip()
                self._save_profile("difficulties", value)
                return

    # -----------------------------
    # EVENT EXTRACTION
    # -----------------------------
    def _extract_events(self, text):
        if "sınav" in text:
            self._save_memory("event", text, importance=3)

        elif "mutluyum" in text or "çok iyi" in text:
            self._save_memory("emotion_positive", text, importance=2)

        elif "üzgünüm" in text or "kötü" in text:
            self._save_memory("emotion_negative", text, importance=4)

    # -----------------------------
    # SAVE HELPERS
    # -----------------------------
    def _save_profile(self, key, value):
        try:
            self.mm.update_person_profile(key, value)
        except Exception as e:
            print(f"[MEMORY WRITER ERROR - PROFILE] {e}")

from memory.embedder import Embedder
from memory.vector_index import VectorIndex

class MemoryWriter:
    def __init__(self, memory_manager):
        self.mm = memory_manager
        self.embedder = Embedder()
        self.vector = VectorIndex()

    def _save_memory(self, tag, text, importance=1):
        try:
            timestamp = int(time.time())

            self.mm.add_episodic_memory(
                content=text,
                tag=tag,
                importance=importance,
                timestamp=timestamp
            )

            vec = self.embedder.embed(text)

            self.vector.add(vec, {
                "content": text,
                "tag": tag,
                "importance": importance,
                "timestamp": timestamp
            })

        except Exception as e:
            print(f"[MEMORY WRITER ERROR] {e}")
