import time
from datetime import date

from memory.memory_manager import MemoryManager
from memory.memory_writer import MemoryWriter
from memory.memory_retriever import MemoryRetriever
from .models import BrainResult
from .response_policy import ResponsePolicy


SYSTEM_PROMPT = """
Sen Poodle'sın.
Tanem için güvenli, sıcak, kısa konuşan bir robot arkadaş ve eğitim koçusun.

Kurallar:
- Asla "Ben bir AI'yım", "Ben bir yapay zeka sistemiyim", "LLM'im" deme.
- Asla İngilizce cevap verme.
- Kısa ve doğal Türkçe konuş.
- Genelde 1-2 kısa cümle kur.
- Gereksiz giriş yapma.
- Kullanıcının söylediği şeye doğrudan cevap ver.
- 13 yaş kullanıcıya uygun, sıcak ve sade ol.
- Bilmediğin bir şeyi uydurma.
- Sorularda mümkünse robot gibi değil arkadaş gibi konuş.
""".strip()


class PoodleBrain:
    def __init__(self, llm):
        self.llm = llm
        self.memory = MemoryManager()
        self.writer = MemoryWriter(self.memory)
        self.retriever = MemoryRetriever(self.memory)
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

        # RAG WRITE
        try:
            self.writer.process(text)
        except Exception as e:
            print(f">>> [MEMORY WRITER ERROR] {e}")

        intent = self.detect_intent(text)
        source_decision = self.policy.choose_source(text, intent)

        if source_decision.source == "clarify":
            return self._log_and_return(
                text=text,
                intent=intent,
                source="clarify",
                reply=source_decision.clarify_text or "Biraz daha açık söyler misin?",
                session_id=session_id,
            )

        direct = self._direct_reply(text, intent)
        if direct:
            return self._log_and_return(
                text=text,
                intent=intent,
                source=source_decision.source,
                reply=direct,
                session_id=session_id,
            )

        template = self._get_template(intent)
        if template and source_decision.source == "template":
            reply = self.policy.apply(template)
            return self._log_and_return(
                text=text,
                intent=intent,
                source="template",
                reply=reply,
                session_id=session_id,
            )

        # RAG READ
        try:
            context = self.retriever.get_context(text)
        except Exception as e:
            print(f">>> [MEMORY RETRIEVER ERROR] {e}")
            context = ""
        
        prompt = f"{SYSTEM_PROMPT}\n{context}\nKullanıcı: {text}"
{SYSTEM_PROMPT}

{context}

Kullanıcı: {text}
""".strip()

        memory_used = bool(context.strip())

        start = time.perf_counter()
        raw = None
        error = None

        try:
            raw = self.llm.generate(prompt)
        except Exception as e:
            error = str(e)

        latency = int((time.perf_counter() - start) * 1000)
        model = getattr(self.llm, "model_name", None) or getattr(self.llm, "model", "unknown")

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
            reply = "Bunu daha sade sorar mısın?"

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

    def _direct_reply(self, text, intent):
        if intent == "greeting":
            return "Selam!"

        if intent == "ask_name":
            return "Ben Poodle."

        if intent == "ask_identity":
            return "Ben Poodle. Seninle konuşan robot arkadaşınım."

        if intent == "ask_status":
            return "İyiyim. Sen nasılsın?"

        if intent == "thanks":
            return "Rica ederim."

        if intent == "farewell":
            return "Görüşürüz."

        if intent == "user_name_define":
            remembered = self._remembered_name()
            if remembered:
                return f"Tamam. Sana {remembered} diyeyim."
            return "Tamam. Öyle diyeyim."

        if intent == "ask_user_name":
            remembered = self._remembered_name()
            if remembered:
                return f"Senin adın {remembered}."
            return "Adını henüz bilmiyorum. Söylersen hatırlamaya çalışırım."

        if intent == "conversation_start":
            return "Tamam. Ne hakkında konuşalım?"

        return None

    def detect_intent(self, text):
        t = self._normalize(text)

        if "merhaba" in t or "selam" in t:
            if "nasilsin" in t:
                return "ask_status"
            return "greeting"

        if "senin adin ne" in t or "adın ne" in text.lower():
            return "ask_name"

        if "kimsin" in t or "kendini tanimlar misin" in t or "kendini tanımlar mısın" in text.lower():
            return "ask_identity"

        if "nasilsin" in t or "nasılsın" in text.lower() or "iyi misin" in t:
            return "ask_status"

        if "tesekkur" in t or "teşekkür" in text.lower() or "sagol" in t or "sağol" in text.lower():
            return "thanks"

        if "gorusuruz" in t or "görüşürüz" in text.lower() or "hosca kal" in t or "hoşça kal" in text.lower():
            return "farewell"

        if "bana " in t and " diyebilirsin" in t:
            return "user_name_define"

        if "benim adim nedir" in t or "benim adım nedir" in text.lower() or "adim ne" in t:
            return "ask_user_name"

        if "konusalim" in t or "konuşalım" in text.lower():
            return "conversation_start"

        return "general"

    def _get_template(self, intent):
        try:
            return self.memory.get_template(intent_name=intent)
        except TypeError:
            try:
                return self.memory.get_template(intent)
            except Exception:
                return None
        except Exception:
            return None

    def _remembered_name(self):
        try:
            p = self.memory.get_person_by_role("tanem")
            if p and p.get("name"):
                return p["name"]
        except Exception:
            pass
        return None

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

    def _normalize(self, text):
        return (text or "").strip().lower()
