import time
from datetime import date
from typing import Optional

from memory.memory_manager import MemoryManager
from memory.memory_writer import MemoryWriter
from memory.memory_retriever import MemoryRetriever
from memory.faiss_adapter import FaissAdapter
from .models import BrainResult
from .response_policy import ResponsePolicy


SYSTEM_PROMPT = """
Sen Poodle'sın.
Tanem için güvenli, sıcak, öğretici ve doğal konuşan bir robot arkadaşsın.

Genel kurallar:
- Sadece Türkçe yaz.
- İngilizce kelime kullanma.
- Yapay zeka, model, sistem veya LLM olduğunu söyleme.
- Bilmediğin bilgiyi uydurma.
- Bağlam verildiyse bağlama sadık kal.
- Cevabın pratik değer taşısın.
- Gereksiz tekrar yapma.
- Sorulan soruya doğrudan cevap ver.
""".strip()


EDUCATION_PROMPT = """
Bu konuşma eğitim modundadır.

Kurallar:
- Öğrenci seviyesinde açık ve öğretici anlat.
- Gerektiğinde biraz detay ver.
- Bağlamdaki bilgilerden ayrılma.
- Konu soruluyorsa tanım + kısa açıklama + mümkünse küçük örnek ver.
- Strateji soruluyorsa uygulanabilir öneriler ver.
- Konu listesi soruluyorsa başlıkları düzenli biçimde ver.
- Sorunun cevabı bağlamda yoksa bunu dürüstçe söyle ve genel, güvenli bir çerçeve sun.
""".strip()


GENERAL_PROMPT = """
Bu konuşma genel moddadır.

Kurallar:
- Cevabın açık, doğal ve faydalı olsun.
- Gereksiz karakter oyunu yapma.
- Kısa sorulara yüzeysel değil, anlamlı cevap ver.
""".strip()


class PoodleBrain:
    def __init__(self, llm):
        self.llm = llm
        self.memory = MemoryManager()
        self.faiss = FaissAdapter()
        self.writer = MemoryWriter(self.memory)
        self.retriever = MemoryRetriever(self.memory, self.faiss)
        self.policy = ResponsePolicy()
        self._run_daily_maintenance_if_needed()

    def _run_daily_maintenance_if_needed(self):
        marker = ".last_maintenance"

        try:
            with open(marker, "r", encoding="utf-8") as f:
                last = f.read().strip()
        except Exception:
            last = None

        today = date.today().isoformat()
        if last == today:
            return

        try:
            self.memory.cleanup_logs()
            self.memory.rebuild_daily_metrics()

            with open(marker, "w", encoding="utf-8") as f:
                f.write(today)

            print(">>> [MAINTENANCE DONE]")
        except Exception as e:
            print(f">>> [MAINTENANCE ERROR] {e}")

    def handle_user_input(self, text, session_id=None):
        return self.handle(text, session_id=session_id)

    def handle(self, text, session_id=None):
        text = (text or "").strip()

        if not text:
            return self._log_and_return(
                text="",
                intent="clarification_needed",
                source="clarify",
                reply="Biraz daha açık söyler misin?",
                session_id=session_id,
            )

        try:
            self.writer.process(text)
        except Exception as e:
            print(f">>> [MEMORY WRITER ERROR] {e}")

        intent = self.detect_intent(text)
        mode = self._detect_mode(text, intent)

        fast = self._try_fast_track(text, intent, mode)
        if fast:
            return self._log_and_return(
                text=text,
                intent=intent,
                source="fast_track",
                reply=fast,
                session_id=session_id,
            )

        direct = self._direct_reply(text, intent)
        if direct:
            return self._log_and_return(
                text=text,
                intent=intent,
                source="direct",
                reply=direct,
                session_id=session_id,
            )

        template = self._get_template(intent)
        if template and intent in {"ask_identity", "ask_name", "ask_user_name", "user_name_define"}:
            return self._log_and_return(
                text=text,
                intent=intent,
                source="template",
                reply=template,
                session_id=session_id,
            )

        if self._should_clarify(text, intent):
            return self._log_and_return(
                text=text,
                intent=intent,
                source="clarify",
                reply="Son kısmı tam anlayamadım. Bir kez daha söyler misin?",
                session_id=session_id,
            )

        bundle = self.retriever.get_context_bundle(
            text=text,
            intent=intent,
            mode=mode,
            top_k=4,
        )

        context = bundle["context_text"]
        confidence = float(bundle["confidence"])
        memory_used = bool(context.strip())

        prompt = self._build_prompt(
            text=text,
            intent=intent,
            mode=mode,
            context=context,
            confidence=confidence,
        )

        start = time.perf_counter()
        raw = None
        error = None

        try:
            raw = self.llm.generate(prompt)
        except Exception as e:
            error = str(e)

        latency = int((time.perf_counter() - start) * 1000)
        model = getattr(self.llm, "model_name", None) or getattr(self.llm, "model", "unknown")

        self._log_llm_call(
            session_id=session_id,
            intent=intent,
            model=model,
            prompt=prompt,
            raw=raw,
            latency=latency,
            error=error,
        )

        if error:
            return self._log_and_return(
                text=text,
                intent=intent,
                source="llm",
                reply="Şu an cevap verirken küçük bir sorun oldu.",
                session_id=session_id,
                model=model,
                latency=latency,
                memory_used=memory_used,
                status="error",
                error=error,
            )

        reply = self.policy.apply(raw)
        if not reply:
            reply = "Bunu bir kez daha söyler misin?"

        return self._log_and_return(
            text=text,
            intent=intent,
            source="llm",
            reply=reply,
            session_id=session_id,
            model=model,
            latency=latency,
            memory_used=memory_used,
        )

    def ask_poodle_stream(self, text, session_id=None):
        text = (text or "").strip()

        if not text:
            yield {"type": "final", "text": "Biraz daha açık söyler misin?", "source": "clarify"}
            return

        try:
            self.writer.process(text)
        except Exception as e:
            print(f">>> [MEMORY WRITER ERROR] {e}")

        intent = self.detect_intent(text)
        mode = self._detect_mode(text, intent)

        fast = self._try_fast_track(text, intent, mode)
        if fast:
            self._log_and_return(
                text=text,
                intent=intent,
                source="fast_track",
                reply=fast,
                session_id=session_id,
            )
            yield {"type": "final", "text": fast, "source": "fast_track", "intent": intent}
            return

        direct = self._direct_reply(text, intent)
        if direct:
            self._log_and_return(
                text=text,
                intent=intent,
                source="direct",
                reply=direct,
                session_id=session_id,
            )
            yield {"type": "final", "text": direct, "source": "direct", "intent": intent}
            return

        template = self._get_template(intent)
        if template and intent in {"ask_identity", "ask_name", "ask_user_name", "user_name_define"}:
            self._log_and_return(
                text=text,
                intent=intent,
                source="template",
                reply=template,
                session_id=session_id,
            )
            yield {"type": "final", "text": template, "source": "template", "intent": intent}
            return

        if self._should_clarify(text, intent):
            reply = "Son kısmı tam anlayamadım. Bir kez daha söyler misin?"
            self._log_and_return(
                text=text,
                intent=intent,
                source="clarify",
                reply=reply,
                session_id=session_id,
            )
            yield {"type": "final", "text": reply, "source": "clarify", "intent": intent}
            return

        bundle = self.retriever.get_context_bundle(
            text=text,
            intent=intent,
            mode=mode,
            top_k=4,
        )

        context = bundle["context_text"]
        confidence = float(bundle["confidence"])
        memory_used = bool(context.strip())

        prompt = self._build_prompt(
            text=text,
            intent=intent,
            mode=mode,
            context=context,
            confidence=confidence,
        )

        start = time.perf_counter()
        model = getattr(self.llm, "model_name", None) or getattr(self.llm, "model", "unknown")
        chunks = []
        error = None

        try:
            for chunk in self.llm.stream(prompt):
                chunks.append(chunk)
                yield {"type": "chunk", "text": chunk, "source": "llm", "intent": intent}
        except Exception as e:
            error = str(e)

        latency = int((time.perf_counter() - start) * 1000)
        raw = "".join(chunks).strip()

        self._log_llm_call(
            session_id=session_id,
            intent=intent,
            model=model,
            prompt=prompt,
            raw=raw,
            latency=latency,
            error=error,
        )

        if error:
            reply = "Şu an cevap verirken küçük bir sorun oldu."
            self._log_and_return(
                text=text,
                intent=intent,
                source="llm",
                reply=reply,
                session_id=session_id,
                model=model,
                latency=latency,
                memory_used=memory_used,
                status="error",
                error=error,
            )
            yield {"type": "final", "text": reply, "source": "llm", "intent": intent}
            return

        reply = self.policy.apply(raw)
        if not reply:
            reply = "Bunu bir kez daha söyler misin?"

        self._log_and_return(
            text=text,
            intent=intent,
            source="llm",
            reply=reply,
            session_id=session_id,
            model=model,
            latency=latency,
            memory_used=memory_used,
        )

        yield {"type": "done", "text": reply, "source": "llm", "intent": intent}

    def _build_prompt(self, text: str, intent: str, mode: str, context: str, confidence: float) -> str:
        parts = [SYSTEM_PROMPT]

        if mode == "education":
            parts.append(EDUCATION_PROMPT)
        else:
            parts.append(GENERAL_PROMPT)

        depth_instruction = self._depth_instruction(intent=intent, mode=mode, confidence=confidence)
        parts.append(depth_instruction)

        if context:
            parts.append("Bağlam:")
            parts.append(context)
        else:
            parts.append("Bağlam: Kullanılabilir ek bağlam bulunamadı. Güvenli ve dürüst kal.")

        parts.append(f"Soru: {text}")
        parts.append("Cevap:")

        return "\n\n".join(parts).strip()

    def _depth_instruction(self, intent: str, mode: str, confidence: float) -> str:
        if mode == "education":
            if intent == "education_topics":
                return (
                    "Yanıt biçimi: Konu başlıklarını düzenli ver. "
                    "İstenirse kısa açıklama ekle. "
                    "Bağlam güçlü ise biraz detay verebilirsin."
                )

            if intent == "exam_support":
                return (
                    "Yanıt biçimi: Önce kısa çerçeve ver, sonra 2-4 uygulanabilir öneri sun. "
                    "Bağlam güçlü ise biraz derinleşebilirsin."
                )

            if intent == "concept_explanation":
                return (
                    "Yanıt biçimi: Önce tanımı ver, sonra sade açıklama yap, sonra kısa örnek ekle. "
                    "Bağlam güçlü ise biraz ayrıntı verebilirsin."
                )

        if confidence >= 0.75:
            return "Yanıt biçimi: Bağlam güçlü. Daha değerli ve açıklayıcı cevap ver, ama konu dışına çıkma."
        if confidence >= 0.45:
            return "Yanıt biçimi: Orta derinlikte, sade ve faydalı cevap ver."
        return "Yanıt biçimi: Kısa ama anlamlı ve dürüst cevap ver."

    def _try_fast_track(self, text: str, intent: str, mode: str) -> Optional[str]:
        # Fast-track sadece gerçekten deterministik alanlar için
        hard_intents = {"greeting", "ask_name", "ask_identity", "audio_check", "thanks", "farewell"}

        if intent in hard_intents:
            answer = self.memory.search_fast_answer(text, intent=intent)
            if answer:
                return answer

        # Eğitim tarafında sadece çok temel exact-match cevapları fast-track et
        if mode == "education" and intent == "education_topics":
            answer = self.memory.search_fast_answer(text, intent=intent)
            if answer:
                return answer

        return None

    def _direct_reply(self, text: str, intent: str) -> Optional[str]:
        if intent == "conversation_start":
            return "Tamam. Ne hakkında konuşalım?"

        return None

    def detect_intent(self, text: str) -> str:
        t = self._normalize(text)
        raw = text.lower()

        if "merhaba" in t or "selam" in t:
            if "nasilsin" in t:
                return "ask_status"
            return "greeting"

        if "nasilsin" in t or "iyi misin" in t:
            return "ask_status"

        if "tesekkur" in t or "sağol" in raw or "sagol" in t:
            return "thanks"

        if "gorusuruz" in t or "hosca kal" in t:
            return "farewell"

        if "adın ne" in raw or "senin adin ne" in t or "senin adın ne" in raw:
            return "ask_name"

        if "kendini tanimlar misin" in t or "kendini tanımlar mısın" in raw or "kimsin" in t:
            return "ask_identity"

        if "bana " in t and " diyebilirsin" in t:
            return "user_name_define"

        if "benim adim nedir" in t or "benim adım nedir" in raw:
            return "ask_user_name"

        if "beni duyabiliyor musun" in raw or "beni duyabiliyormusun" in raw:
            return "audio_check"

        if (
            "lgs konular" in t
            or "dgs konular" in t
            or "hangi konular" in t
            or "konulari listeler misin" in t
            or "konuları listeler misin" in raw
            or "odaklanmam gerektigini" in t
            or "odaklanmam gerektiğini" in raw
        ):
            return "education_topics"

        if (
            "sinav stresi" in t
            or "sınav stresi" in raw
            or "ozet verir misin" in t
            or "özet verir misin" in raw
            or "nasil calismaliyim" in t
            or "nasıl çalışmalıyım" in raw
            or "strateji" in t
            or "taktik" in t
        ):
            return "exam_support"

        if (
            "nedir" in t
            or "anlatir misin" in t
            or "anlatır mısın" in raw
            or "detay verir misin" in raw
        ):
            return "concept_explanation"

        if "konusalim" in t or "konuşalım" in raw:
            return "conversation_start"

        return "general"

    def _detect_mode(self, text: str, intent: str) -> str:
        t = self._normalize(text)

        if intent in {"education_topics", "exam_support", "concept_explanation"}:
            return "education"

        education_tokens = {
            "lgs", "dgs", "sinav", "ders", "matematik", "turkce",
            "inkilap", "fen", "ingilizce", "din", "konu", "ozet",
            "sayi", "cebir", "geometri", "karekok", "uslu"
        }

        if any(tok in t for tok in education_tokens):
            return "education"

        return "general"

    def _should_clarify(self, text: str, intent: str) -> bool:
        if intent in {
            "greeting", "ask_status", "thanks", "ask_name",
            "ask_identity", "audio_check", "user_name_define",
            "ask_user_name", "education_topics", "exam_support",
            "concept_explanation", "conversation_start"
        }:
            return False

        t = self._normalize(text)

        if len(t.split()) <= 1:
            return True

        bad_fragments = ["in club", "now see", "sinov sinov", "3 stres"]
        if any(x in t for x in bad_fragments):
            return True

        return False

    def _get_template(self, intent: str) -> Optional[str]:
        try:
            return self.memory.get_template(intent_name=intent)
        except Exception:
            return None

    def _log_llm_call(self, session_id, intent, model, prompt, raw, latency, error):
        try:
            self.memory.log_llm_call(
                session_id=session_id,
                intent=intent,
                model_name=model,
                prompt_chars=len(prompt),
                response_chars=len(raw) if raw else 0,
                latency_ms=latency,
                status="error" if error else "ok",
                error_text=error,
            )
        except Exception as e:
            print(f">>> [LOG LLM ERROR] {e}")

    def _log_and_return(
        self,
        text,
        intent,
        source,
        reply,
        session_id=None,
        model=None,
        latency=None,
        memory_used=False,
        status="ok",
        error=None,
    ):
        normalized = self._normalize(text)

        try:
            self.memory.log_conversation(
                raw_text=text,
                normalized_text=normalized,
                intent=intent,
                response_source=source,
                reply_text=reply,
            )
        except Exception as e:
            print(f">>> [LOG CONVERSATION ERROR] {e}")

        try:
            self.memory.log_conversation_telemetry(
                session_id=session_id,
                intent=intent,
                response_source=source,
                model_name=model,
                latency_ms=latency,
                memory_context_used=memory_used,
                status=status,
                error_text=error,
            )
        except Exception as e:
            print(f">>> [LOG TELEMETRY ERROR] {e}")

        return BrainResult(reply_text=reply, intent=intent)

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
