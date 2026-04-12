from dataclasses import dataclass
from typing import Optional
import re


@dataclass
class Decision:
    source: str
    clarify_text: Optional[str] = None


class ResponsePolicy:
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
            "ask_topic",
            "open_topic",
            "ask_user_name",
            "user_name_define",
            "education_topics",
            "audio_check",
        }

        self.banned_phrases = [
            "ben bir ai",
            "yapay zeka",
            "artificial intelligence",
            "language model",
            "llm",
            "ben bir sistemim",
            "ai system",
            "as an ai",
            "i am an ai",
            "ben sen poodle",
            "sen poodle'sın",
            "sen poodlesin",
            "size yardımcı olmaktan memnuniyet duyarım",
            "lütfen sorularınızı bildirin",
            "bilgi vermemeyeceğim",
            "veremem",
            "yardımcı olmak için buradayım",
        ]

        self.noise_terms = [
            "hıznav",
            "naw stress",
            "naw stressi",
            "now see to see",
            "sinov",
            "in club",
            "3 stres",
        ]

        self.bad_openings = [
            "merhaba tanem",
            "merhaba",
            "selam tanem",
            "selam",
            "hey",
            "tanem",
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

        if len(t.split()) <= 2 and intent == "general":
            return Decision("clarify", "Biraz daha açık söyler misin?")

        return Decision("llm")

    # =========================================================
    # POST-PROCESS
    # =========================================================
    def apply(self, raw: str) -> str:
        if not raw:
            return "Biraz daha açık söyler misin?"

        text = self._cleanup_whitespace(raw)
        lower = text.lower()

        # 1) ağır persona / meta kaçakları direkt fallback'e çevir
        if self._contains_banned_phrase(lower):
            return "Bunu daha kısa ve net söyleyeyim. Sorunu tekrar sorar mısın?"

        # 2) gürültülü / saçma içerikleri temizle
        if self._contains_noise_term(lower):
            return "Bunu tam net anlayamadım. Bir kez daha söyler misin?"

        # 3) açılış, meta ve robotik kısımları sök
        text = self._strip_bad_opening(text)
        text = self._strip_meta_robotic(text)

        # 4) tekrar normalize et
        text = self._cleanup_whitespace(text)

        # 5) boş kaldıysa güvenli fallback
        if not text or len(text.strip()) < 3:
            return "Bunu daha kısa ve net söyler misin?"

        # 6) eğitim stiline çek
        text = self._make_child_friendly(text)

        # 7) uzunluğu sıkı kontrol et
        text = self._limit_sentences(text, max_sentences=2)
        text = self._limit_words(text, max_words=20)

        # 8) yine boş / bozuksa fallback
        if not text or len(text.strip()) < 3:
            return "Bunu daha kısa ve net söyler misin?"

        # 9) tekrar cevabı engelle
        if self.last_reply and self._is_too_similar(text, self.last_reply):
            text = self._diversify(text)

        self.last_reply = text
        return text.strip()

    # =========================================================
    # CHECKS
    # =========================================================
    def _contains_banned_phrase(self, lower: str) -> bool:
        return any(p in lower for p in self.banned_phrases)

    def _contains_noise_term(self, lower: str) -> bool:
        return any(p in lower for p in self.noise_terms)

    def _looks_like_noise_input(self, text: str) -> bool:
        if len(text) < 4:
            return True

        if len(text.split()) == 1 and text not in {"merhaba", "selam", "teşekkür", "sağol"}:
            return True

        if any(term in text for term in self.noise_terms):
            return True

        # çok bozuk karakter / tekrar yapısı
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
            "robot arkadaşın ve eğitim koçusum": "robot arkadaşınım",
            "robot arkadaşın ve eğitim koçuyum": "robot arkadaşınım",
            "Güzel günler dilerim": "",
            "yardımcı olmak için buradayım": "",
            "bilgi vermemeyeceğim": "kısa anlatayım",
            "olacam": "olurum",
            "gerçekten mi": "",
            "neden mi": "",
            "sayın kullanıcı": "",
        }

        result = text
        for old, new in replacements.items():
            result = result.replace(old, new)
            result = result.replace(old.lower(), new)

        return result.strip()

    def _make_child_friendly(self, text: str) -> str:
        result = text.strip()

        replacements = {
            "zorundasın": "yapabilirsin",
            "yapmalısın": "yapabilirsin",
            "mutlaka": "öncelikle",
            "karmaşık": "biraz zor",
            "komplike": "biraz zor",
            "Hayır,": "",
            "Hayır!": "",
            "Hayır, hayır!": "Şöyle diyeyim.",
            "Aslında": "",
            "Özetle": "Kısaca",
        }

        for old, new in replacements.items():
            result = result.replace(old, new)

        # fazla ünlem / soru işareti temizliği
        result = result.replace("!!", "!")
        result = result.replace("??", "?")
        result = re.sub(r"\s+", " ", result).strip()

        # bazı istenmeyen ton kalıpları
        banned_patterns = [
            r"\bçok ilgincikler\b",
            r"\bseneye yeni şeyler öğreniyorum\b",
            r"\bbu konuda hiç altyazım yok\b",
            r"\bgüzel günler dilerim\b",
        ]
        for pattern in banned_patterns:
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
    def _limit_sentences(self, text: str, max_sentences: int = 2) -> str:
        parts = self._split_sentences(text)
        if len(parts) <= max_sentences:
            return text.strip()

        return " ".join(parts[:max_sentences]).strip()

    def _limit_words(self, text: str, max_words: int = 20) -> str:
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
    # SIMILARITY / DIVERSIFY
    # =========================================================
    def _is_too_similar(self, a: str, b: str) -> bool:
        a_tokens = set(self._normalize(a).split())
        b_tokens = set(self._normalize(b).split())

        if not a_tokens or not b_tokens:
            return False

        overlap = len(a_tokens & b_tokens) / max(len(a_tokens), 1)
        return overlap > 0.75

    def _diversify(self, text: str) -> str:
        short_forms = [
            "Kısaca şöyle:",
            "Şöyle diyeyim:",
            "Daha kısa anlatayım:",
        ]

        base = self._cleanup_whitespace(text)
        if not base:
            return "Bunu daha kısa ve net söyler misin?"

        return f"{short_forms[0]} {base}"

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
