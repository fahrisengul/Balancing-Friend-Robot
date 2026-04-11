from datetime import datetime
import re

from .embedder import Embedder
from .vector_index import VectorIndex


class MemoryWriter:
    def __init__(self, memory_manager):
        self.memory = memory_manager
        self.embedder = Embedder()
        self.index = VectorIndex()

        self.transient_patterns = [
            "merhaba",
            "selam",
            "nasılsın",
            "nasilsin",
            "teşekkür",
            "tesekkur",
            "sağol",
            "sagol",
            "görüşürüz",
            "gorusuruz",
            "beni duyabiliyor musun",
            "beni duyabiliyormusun",
            "duyuyor musun",
            "duyuyormusun",
        ]

    def process(self, text: str):
        text = self._clean_text(text)
        if not text:
            return

        memory_type = self._classify_memory_type(text)

        if memory_type == "discard":
            print(f">>> [MEMORY FILTER] discard: {text}")
            return

        # profile memory
        name = self._extract_name(text)
        if name:
            self._save_name(name)

        # episodic memory
        if memory_type == "episodic":
            self._save_memory(text, category="episodic", importance=2)

    # =========================================================
    # TYPE
    # =========================================================
    def _classify_memory_type(self, text: str) -> str:
        t = text.lower()

        if self._is_noise(text):
            return "discard"

        if self._extract_name(text):
            return "profile"

        if any(x in t for x in [
            "sınav",
            "sinav",
            "lgs",
            "okul",
            "ders",
            "ödev",
            "odev",
            "stres",
            "kaygı",
            "kaygi",
            "seviyorum",
            "istemiyorum",
            "hoşlanıyorum",
            "hoslaniyorum",
            "konuşmak istiyorum",
            "konusmak istiyorum",
        ]):
            return "episodic"

        # Genel ama anlamlı sayılabilecek uzun kullanıcı ifadeleri
        if len(text.split()) >= 5 and self._is_coherent_enough(text):
            return "episodic"

        return "discard"

    # =========================================================
    # FILTER
    # =========================================================
    def _is_noise(self, text: str) -> bool:
        t = text.lower().strip()

        if len(t) < 8:
            return True

        if len(t.split()) < 3:
            return True

        if any(p == t for p in self.transient_patterns):
            return True

        # Tekrar eden anlamsız kısa yapı
        if self._has_too_much_repetition(t):
            return True

        # Çok fazla latin karışık / anlamsız token
        if self._looks_like_stt_garbage(t):
            return True

        return False

    def _is_coherent_enough(self, text: str) -> bool:
        t = text.lower()

        vowels = sum(1 for c in t if c in "aeıioöuü")
        alpha = sum(1 for c in t if c.isalpha())

        if alpha == 0:
            return False

        vowel_ratio = vowels / alpha

        # aşırı bozuk metinleri ele
        if vowel_ratio < 0.18:
            return False

        return True

    def _has_too_much_repetition(self, text: str) -> bool:
        words = text.split()
        if not words:
            return True

        unique_ratio = len(set(words)) / len(words)
        return unique_ratio < 0.45

    def _looks_like_stt_garbage(self, text: str) -> bool:
        # İngilizce kırıntılı, anlamsız STT örnekleri
        bad_fragments = [
            "now see",
            "naw",
            "hıznav",
            "sinov sinov",
            "evliyorum",
        ]
        return any(frag in text for frag in bad_fragments)

    def _clean_text(self, text: str) -> str:
        text = (text or "").strip()
        text = re.sub(r"\s+", " ", text)
        return text

    # =========================================================
    # NAME
    # =========================================================
    def _extract_name(self, text: str):
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

    # =========================================================
    # SAVE
    # =========================================================
    def _save_memory(self, text: str, category="episodic", importance=2):
        try:
            # aynı veya çok benzer kayıt varsa yeniden yazma
            recent = self.memory.search_memories(text, limit=3)
            if any(self._normalize(x) == self._normalize(text) for x in recent):
                print(f">>> [MEMORY FILTER] duplicate: {text}")
                return

            vector = self.embedder.embed(text)

            memory_id = self.memory.add_episodic_memory(
                content=text,
                timestamp=datetime.utcnow().isoformat(),
                category=category,
                importance=importance,
            )

            self.index.add(vector, memory_id)

        except Exception as e:
            print(f">>> [VECTOR SAVE ERROR] {e}")

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
        t = re.sub(r"[^a-z0-9\s]", " ", t)
        t = re.sub(r"\s+", " ", t).strip()
        return t
