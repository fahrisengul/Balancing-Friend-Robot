import time
from datetime import date
from typing import Optional, Dict, Any

from memory.memory_manager import MemoryManager
from memory.memory_writer import MemoryWriter
from memory.memory_retriever import MemoryRetriever
from .models import BrainResult
from .response_policy import ResponsePolicy


SYSTEM_PROMPT = (
    "Sen Poodle'sın. "
    "13 yaş için güvenli, sıcak, kısa konuşan bir eğitim robotusun. "
    "Asla yapay zeka, model, sistem, LLM olduğunu söyleme. "
    "Asla düşünme sürecini anlatma. "
    "Sorulan soruya doğrudan cevap ver. "
    "Bilmediğin bilgiyi uydurma. "
    "Maksimum 3 kısa cümle kullan. "
    "Maksimum 20 kelimeyi hedefle. "
    "Gereksiz selamlama ve tekrar yapma. "
    "Tanem adına doğal ama abartısız hitap et. "
    "Özellikle eğitim, sınav, ders ve konu sorularında öğretici, sade ve doğru ol."
)

EDUCATION_PROMPT = (
    "Bu konuşma eğitim modundadır. "
    "Öğrenci seviyesinde, sade ve doğru anlat. "
    "Kısa cevap ver. "
    "Gerekirse en fazla 3 maddede açıkla. "
    "Yanlış bilgi verme. "
    "Konu listesi istenirse sadece ilgili konu başlıklarını ver. "
    "Özet istenirse kısa özet ver. "
    "Tanım istenirse kısa tanım ve bir küçük örnek ver."
)


class PoodleBrain:
    def __init__(self, llm):
        self.llm = llm
        self.memory = MemoryManager()
        self.writer = MemoryWriter(self.memory)
        self.retriever = MemoryRetriever(self.memory)
        self.policy = ResponsePolicy()
        self._run_daily_maintenance_if_needed()

    # =========================================================
    # MAINTENANCE
    # =========================================================
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

    # =========================================================
    # PUBLIC API
    # =========================================================
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

        # memory write
        try:
            self.writer.process(text)
        except Exception as e:
            print(f">>> [MEMORY WRITER ERROR] {e}")

        intent = self.detect_intent(text)
        mode = self._detect_mode(text, intent)

        # 1) hard fast-track
        fast = self._try_fast_track(text, intent, mode)
        if fast:
            return self._log_and_return(
                text=text,
                intent=intent,
                source="fast_track",
                reply=fast,
                session_id=session_id,
            )

        # 2) deterministic direct reply
        direct = self._direct_reply(text, intent)
        if direct:
            return self._log_and_return(
                text=text,
                intent=intent,
                source="direct",
                reply=direct,
                session_id=session_id,
            )

        # 3) template
        template = self._get_template(intent)
        if template:
            reply = self.policy.apply(template)
            return self._log_and_return(
                text=text,
                intent=intent,
                source="template",
                reply=reply,
                session_id=session_id,
            )

        # 4) very short / noisy / unclear
        if self._should_clarify(text, intent):
            return self._log_and_return(
                text=text,
                intent=intent,
                source="clarify",
                reply="Son kısmı tam anlayamadım. Bir kez daha söyler misin?",
                session_id=session_id,
            )

        # 5) build context only when useful
        context = self._build_context(text, intent, mode)
        memory_used = bool(context.strip())

        # 6) llm fallback
        prompt = self._build_prompt(text, context, mode)

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
                reply="Bir sorun oldu ama tekrar deneyebiliriz.",
                session_id=session_id,
                model=model,
                latency=latency,
                memory_used=memory_used,
                status="error",
                error=error,
            )

        reply = self.policy.apply(raw)

        if not reply:
            reply = "Bunu daha kısa ve net söyler misin?"

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

    # =========================================================
    # STREAMING API
    # =========================================================
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
        if template:
            reply = self.policy.apply(template)
            self._log_and_return(
                text=text,
                intent=intent,
                source="template",
                reply=reply,
                session_id=session_id,
            )
            yield {"type": "final", "text": reply, "source": "template", "intent": intent}
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

        context = self._build_context(text, intent, mode)
        memory_used = bool(context.strip())
        prompt = self._build_prompt(text, context, mode)

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
            reply = "Bir sorun oldu ama tekrar deneyebiliriz."
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
            reply = "Bunu daha kısa ve net söyler misin?"

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

    # =========================================================
    # ROUTING
    # =========================================================
    def detect_intent(self, text: str) -> str:
        t = self._normalize(text)

        # basic
        if "merhaba" in t or "selam" in t:
            if "nasilsin" in t:
                return "ask_status"
            return "greeting"

        if "nasilsin" in t or "iyi misin" in t:
            return "ask_status"

        if "tesekkur" in t or "sagol" in t:
            return "thanks"

        if "gorusuruz" in t or "hosca kal" in t:
            return "farewell"

        if "adın ne" in text.lower() or "senin adin ne" in t or "senin adın ne" in text.lower():
            return "ask_name"

        if "kimsin" in t or "kendini tanimlar misin" in t or "kendini tanımlar mısın" in text.lower():
            return "ask_identity"

        if "bana " in t and " diyebilirsin" in t:
            return "user_name_define"

        if "benim adim nedir" in t or "benim adım nedir" in text.lower():
            return "ask_user_name"

        if "beni duyabiliyor musun" in text.lower() or "beni duyabiliyormusun" in text.lower():
            return "audio_check"

        # education
        if (
            "lgs konular" in t
            or "dgs konular" in t
            or "hangi konular" in t
            or "konulari listeler misin" in t
            or "konuları listeler misin" in text.lower()
        ):
            return "education_topics"

        if (
            "sinav stresi" in t
            or "sınav stresi" in text.lower()
            or "nasil calismaliyim" in t
            or "nasıl çalışmalıyım" in text.lower()
            or "odaklanmam gerektigini" in t
            or "odaklanmam gerektiğini" in text.lower()
            or "özet verir misin" in text.lower()
            or "ozet verir misin" in t
        ):
            return "exam_support"

        if (
            "nedir" in t
            or "anlatir misin" in t
            or "anlatır mısın" in text.lower()
            or "detay verir misin" in text.lower()
        ):
            return "concept_explanation"

        if "konusalim" in t or "konuşalım" in text.lower():
            return "conversation_start"

        return "general"

    def _detect_mode(self, text: str, intent: str) -> str:
        t = self._normalize(text)

        if intent in {"education_topics", "exam_support", "concept_explanation"}:
            return "education"

        education_tokens = {
            "lgs", "dgs", "sinav", "ders", "matematik", "turkce",
            "inkilap", "fen", "ingilizce", "din", "konu", "özet", "ozet"
        }

        if any(tok in t for tok in education_tokens):
            return "education"

        return "general"

    def _try_fast_track(self, text: str, intent: str, mode: str) -> Optional[str]:
        # hard fast-track intents
        hard_intents = {
            "greeting", "ask_status", "thanks", "ask_name",
            "audio_check", "farewell", "ask_identity"
        }

        if intent in hard_intents:
            answer = self.memory.search_fast_answer(text, intent=intent)
            if answer:
                return self.policy.apply(answer)

        # education fast answer
        if mode == "education":
            answer = self.memory.search_fast_answer(text, intent=intent)
            if answer:
                return self.policy.apply(answer)

            snippets = self.memory.search_education_snippets(text, limit=2)
            if snippets:
                snippet_text = self._compose_snippet_answer(snippets, intent)
                if snippet_text:
                    return self.policy.apply(snippet_text)

        return None

    def _compose_snippet_answer(self, snippets, intent: str) -> Optional[str]:
        if not snippets:
            return None

        if intent == "education_topics":
            topic_names = []
            seen = set()
            for item in snippets:
                topic = (item.get("topic_name") or "").strip()
                if topic and topic not in seen:
                    seen.add(topic)
                    topic_names.append(topic)

            if topic_names:
                return "İlgili başlıklar: " + ", ".join(topic_names[:5]) + "."

        first = snippets[0].get("content")
        if first:
            return first

        return None

    def _direct_reply(self, text: str, intent: str) -> Optional[str]:
        if intent == "user_name_define":
            remembered = self._remembered_name()
            if remembered:
                return f"Tamam. Sana {remembered} diyeyim."
            return "Tamam."

        if intent == "ask_user_name":
            remembered = self._remembered_name()
            if remembered:
                return f"Senin adın {remembered}."
            return "Adını henüz bilmiyorum. Söylersen hatırlarım."

        if intent == "conversation_start":
            return "Tamam. Ne hakkında konuşalım?"

        return None

    def _should_clarify(self, text: str, intent: str) -> bool:
        t = self._normalize(text)

        if intent in {
            "greeting", "ask_status", "thanks", "ask_name", "ask_identity",
            "audio_check", "user_name_define", "ask_user_name",
            "education_topics", "exam_support", "concept_explanation",
            "conversation_start"
        }:
            return False

        if len(t.split()) <= 1:
            return True

        bad_fragments = ["in club", "now see", "sinov sinov", "3 stres"]
        if any(x in t for x in bad_fragments):
            return True

        return False

    # =========================================================
    # PROMPT / CONTEXT
    # =========================================================
    def _build_context(self, text: str, intent: str, mode: str) -> str:
        # very short or hard deterministic intents -> no RAG
        if intent in {"greeting", "ask_status", "thanks", "ask_name", "audio_check"}:
            return ""

        if len(text.split()) < 4:
            return ""

        try:
            context = self.retriever.get_context(text)
            return context or ""
        except Exception as e:
            print(f">>> [MEMORY RETRIEVER ERROR] {e}")
            return ""

    def _build_prompt(self, text: str, context: str, mode: str) -> str:
        parts = [SYSTEM_PROMPT]

        if mode == "education":
            parts.append(EDUCATION_PROMPT)

        if context:
            parts.append(f"Bağlam:\n{context}")

        parts.append(f"Kullanıcı: {text}")
        parts.append("Poodle:")

        return "\n".join(parts)

    # =========================================================
    # DB HELPERS
    # =========================================================
    def _get_template(self, intent: str) -> Optional[str]:
        try:
            return self.memory.get_template(intent_name=intent)
        except Exception:
            return None

    def _remembered_name(self) -> Optional[str]:
        try:
            p = self.memory.get_person_by_role("tanem")
            if p and p.get("name"):
                return p["name"]
        except Exception:
            pass
        return None

    # =========================================================
    # LOGGING
    # =========================================================
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
