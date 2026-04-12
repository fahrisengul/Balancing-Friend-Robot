from dataclasses import dataclass
from typing import Optional
import re


@dataclass
class Decision:
    source: str
    clarify_text: Optional[str] = None


class ResponsePolicy:
    """
    Yeni strateji:
    - İyi cevapları gereksiz kısaltma
    - Ama bozuk / halüsinatif / meta cevapları yakala
    - Türkçe dışına kayan, hibrit, anlamsız ya da robotik çıktıları temizle
    """

    def __init__(self):
        self.last_reply = None

        self.template_intents = {
            "greeting",
            "farewell",
            "ask_name",
            "ask_identity",
            "ask_status",
            "thanks",
            "conversation_start",
            "ask_user_name",
            "user_name_define",
            "audio_check",
        }

        self.banned_meta_phrases = [
            "ben bir ai",
            "yapay zeka",
            "language model",
            "llm",
            "artificial intelligence",
            "ben bir sistemim",
            "ai system",
            "as an ai",
            "i am an ai",
            "robot arkadaşın ve eğitim koçusum",
            "robot arkadaşın ve eğitim koçuyum",
            "size yardımcı olmaktan memnuniyet duyarım",
            "yardımcı olmak için buradayım",
            "lütfen sorularınızı bildirin",
        ]

        self.bad_noise_terms = [
            "hıznav",
            "naw stress",
            "naw stressi",
            "now see to see",
            "sinov",
            "in club",
            "3 stres",
        ]

        self.bad_mixed_terms = [
            "gemeinschaft",
            "mutual",
            "happinessa",
            "expectasyon",
            "newtör",
            "friendse",
            "ouruzu",
        ]

        self.bad_openings = [
            "merhaba tanem",
            "merhaba",
            "selam tanem",
            "selam",
            "hey",
        ]

    # =========================================================
    # ROUTING DECISION
    # =========================================================
    def choose_source(self, text: str, intent: str) -> Decision:
        t = self._normalize(text)

        if not t:
            return Decision("clarify", "Biraz daha açık söyler misin?")

        if intent in self.template_intents:
            return Decision("template")

        if self._looks_like_noise_input(t):
            return Decision("clarify", "Son kısmı tam anlayamadım. Bir kez daha söyler misin?")

        if len(t.split()) <= 1 and intent == "general":
            return Decision("clarify", "Biraz daha açık söyler misin?")

        return Decision("llm")

    # =========================================================
    # MAIN APPLY
    # =========================================================
    def apply(self, raw: str) -> str:
        if not raw:
            return "Biraz daha açık söyler misin?"

        text = self._cleanup_whitespace(raw)
        lower = text.lower()

        # 1. ağır meta kaçakları
        if self._contains_any(lower, self.banned_meta_phrases):
            return "Bunu daha doğal ve net söyleyeyim. Sorunu tekrar sorar mısın?"

        # 2. gürültü / saçma STT terimleri
        if self._contains_any(lower, self.bad_noise_terms):
            return "Son kısmı tam net anlayamadım. Bir kez daha söyler misin?"

        # 3. kötü hibrit dil
        if self._contains_any(lower, self.bad_mixed_terms):
            cleaned = self._remove_bad_mixed_parts(text)
            if cleaned and len(cleaned.split()) >= 4:
                text = cleaned
            else:
                return "Bunu daha düzgün ve net anlatayım. Sorunu bir kez daha sorar mısın?"

        # 4. açılış ve robotik meta temizliği
        text = self._strip_bad_opening(text)
        text = self._strip_meta_robotic(text)

        # 5. whitespace / punctuation temizliği
        text = self._cleanup_whitespace(text)

        # 6. boş kaldıysa fallback
        if not text or len(text.strip()) < 3:
            return "Bunu daha net söyler misin?"

        # 7. çocuk dostu ama aşırı küçültmeden
        text = self._make_child_friendly(text)

        # 8. cümle sayısını çok sert kısma; ama saçma uzamayı kes
        text = self._limit_sentences(text, max_sentences=4)
        text = self._limit_words(text, max_words=80)

        # 9. tekrar kontrolü
        if not text or len(text.strip()) < 3:
            return "Bunu daha net söyler misin?"

        if self.last_reply and self._is_too_similar(text, self.last_reply):
            text = self._diversify(text)

        self.last_reply = text
        return text.strip()

    # =========================================================
    # CHECKS
    # =========================================================
    def _contains_any(self, text: str, phrases) -> bool:
        return any(p in text for p in phrases)

    def _looks_like_noise_input(self, text: str) -> bool:
        if len(text) < 4:
            return True

        if len(text.split()) == 1 and text not in {"merhaba", "selam", "teşekkür", "sagol", "sağol"}:
            return True

        if self._contains_any(text, self.bad_noise_terms):
            return True

        tokens = text.split()
        if tokens:
            unique_ratio = len(set(tokens)) / len(tokens)
            if len(tokens) >= 4 and unique_ratio < 0.45:
                return True

        return False

    # =========================================================
    # CLEANUP
    # =========================================================
    def _strip_bad_opening(self, text: str) -> str:
        result = text.strip()

        for opening in self.bad_openings:
            pattern = rf"^{re.escape(opening)}[!,.\s:;-]*"
            result = re.sub(pattern, "", result, flags=re.IGNORECASE).strip()

        return result

    def _strip_meta_robotic(self, text: str) -> str:
        replacements = {
            "Ben bir AI sistemiyim": "",
            "Ben bir yapay zeka sistemiyim": "",
            "Ben bir sistemim": "",
            "Artificial Intelligence": "",
            "Güzel günler dilerim": "",
            "yardımcı olmak için buradayım": "",
            "Size yardımcı olmayı umuyorum": "",
            "Tanışalım": "",
            "gerçekten mi": "",
            "neden mi": "",
            "sayın kullanıcı": "",
        }

        result = text
        for old, new in replacements.items():
            result = result.replace(old, new)
            result = result.replace(old.lower(), new)

        return result.strip()

    def _remove_bad_mixed_parts(self, text: str) -> str:
        result = text
        for term in self.bad_mixed_terms:
            result = re.sub(re.escape(term), "", result, flags=re.IGNORECASE)
        result = self._cleanup_whitespace(result)
        return result

    def _make_child_friendly(self, text: str) -> str:
        result = text.strip()

        replacements = {
            "zorundasın": "yapabilirsin",
            "yapmalısın": "yapabilirsin",
            "karmaşık": "biraz zor",
            "komplike": "biraz zor",
            "Aslında": "",
            "Özetle": "Kısaca",
            "Hayır,": "",
            "Hayır!": "",
        }

        for old, new in replacements.items():
            result = result.replace(old, new)

        result = result.replace("!!", "!")
        result = result.replace("??", "?")
        result = re.sub(r"\s+", " ", result).strip()

        # gereksiz garip kalıplar
        bad_patterns = [
            r"\bçok ilgincikler\b",
            r"\bseneye yeni şeyler öğreniyorum\b",
            r"\bbu konuda hiç altyazım yok\b",
            r"\bbilgi vermemeyeceğim\b",
            r"\bouruzu\b",
            r"\bhappinessa\b",
            r"\bexpectasyonlar\b",
        ]
        for pattern in bad_patterns:
            result = re.sub(pattern, "", result, flags=re.IGNORECASE).strip()

        result = self._cleanup_whitespace(result)
        return result

    def _cleanup_whitespace(self, text: str) -> str:
        text = " ".join((text or "").split())
        text = re.sub(r"\s+([,.!?;:])", r"\1", text)
        return text.strip()

    # =========================================================
    # LENGTH CONTROL
    # =========================================================
    def _limit_sentences(self, text: str, max_sentences: int = 4) -> str:
        parts = self._split_sentences(text)
        if len(parts) <= max_sentences:
            return text.strip()
        return " ".join(parts[:max_sentences]).strip()

    def _limit_words(self, text: str, max_words: int = 80) -> str:
        words = text.split()
        if len(words) <= max_words:
            return text.strip()

        clipped = " ".join(words[:max_words]).strip()
        if not clipped.endswith((".", "!", "?")):
            clipped += "."
        return clipped

    def _split_sentences(self, text: str):
        parts = []
        current = ""

        for ch in text:
            current += ch
            if ch in ".!?":
                if current.strip():
                    parts.append(current.strip())
                current = ""

        if current.strip():
            parts.append(current.strip())

        return parts

    # =========================================================
    # SIMILARITY
    # =========================================================
    def _is_too_similar(self, a: str, b: str) -> bool:
        a_tokens = set(self._normalize(a).split())
        b_tokens = set(self._normalize(b).split())

        if not a_tokens or not b_tokens:
            return False

        overlap = len(a_tokens & b_tokens) / max(len(a_tokens), 1)
        return overlap > 0.82

    def _diversify(self, text: str) -> str:
        prefix = "Şöyle diyeyim:"
        base = self._cleanup_whitespace(text)
        if not base:
            return "Bunu daha net söyler misin?"
        return f"{prefix} {base}"

    # =========================================================
    # NORMALIZE
    # =========================================================
    def _normalize(self, text: str) -> str:
        t = (text or "").strip().lower()
        return (
            t.replace("ı", "i")
            .replace("ğ", "g")
            .replace("ş", "s")
            .replace("ç", "c")
            .replace("ö", "o")
            .replace("ü", "u")
        )
