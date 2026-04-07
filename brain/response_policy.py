from dataclasses import dataclass


@dataclass
class Decision:
    source: str
    clarify_text: str | None = None


class ResponsePolicy:

    def choose_source(self, text: str, intent: str) -> Decision:

        t = (text or "").lower().strip()

        # 🔴 BAD input
        if not t or len(t) < 2:
            return Decision("clarify", "Seni tam anlayamadım. Tekrar söyler misin?")

        # 🔹 deterministic/template
        if intent in ["greeting", "ask_name", "ask_identity", "ask_status", "farewell"]:
            return Decision("template")

        # 🔹 repair (çok önemli)
        if intent == "followup_repair":
            return Decision("template")

        # 🔹 gerçek soru → LLM
        if intent == "question":
            return Decision("llm")

        # 🔹 statement → kısa cevap
        if intent == "statement":
            return Decision("template")

        # 🔹 fallback
        return Decision("llm")

    def apply(self, raw: str) -> str:
        if not raw:
            return "Tam anlayamadım. Bir daha söyler misin?"

        text = raw.strip()

        # 🔴 saçma filtre
        banned = ["ahaha", "ooh", "hehe"]
        if any(b in text.lower() for b in banned):
            return "Bunu daha net söyleyebilir misin?"

        # 🔴 İngilizce kaçış
        if any(w in text for w in ["Hello", "Oh", "dear"]):
            return "Türkçe devam edelim. Ne demek istemiştin?"

        # 🔹 uzunluk sınırı
        sentences = text.split(".")
        text = ".".join(sentences[:2]).strip()

        return text
