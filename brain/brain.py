import time
from datetime import date

from memory.memory_manager import MemoryManager
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
- Kullanıcı adını söylüyorsa bunu kabul et ve doğal cevap ver.
- Sorularda mümkünse robot gibi değil arkadaş gibi konuş.
""".strip()


class PoodleBrain:
    def __init__(self, llm):
        self.llm = llm
        self.memory = MemoryManager()
        self.policy = ResponsePolicy()
        self._run_daily_maintenance_if_needed()

    # =========================
    # DAILY MAINTENANCE
    # =========================
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
            if hasattr(self.memory, "cleanup_logs"):
                self.memory.cleanup_logs()
            if hasattr(self.memory, "rebuild_daily_metrics"):
                self.memory.rebuild_daily_metrics()

            with open(marker, "w", encoding="utf-8") as f:
                f.write(today)

            print(">>> [MAINTENANCE DONE]")
        except Exception as e:
            print(f">>> [MAINTENANCE ERROR] {e}")

    # =========================
    # ORCHESTRATOR API
    # =========================
    def handle_user_input(self, text, session_id=None):
        return self.handle(text, session_id=session_id)

    # =========================
    # MAIN ENTRY
    # =========================
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

        intent = self.detect_intent(text)
        source_decision = self.policy.choose_source(text, intent)

        # 1) clarify
        if source_decision.source == "clarify":
            return self._log_and_return(
                text=text,
                intent=intent,
                source="clarify",
                reply=source_decision.clarify_text or "Biraz daha açık söyler misin?",
                session_id=session_id,
            )

        # 2) direct deterministic shortcuts
        direct = self._direct_reply(text, intent)
        if direct:
            return self._log_and_return(
                text=text,
                intent=intent,
                source=source_decision.source,
                reply=direct,
                session_id=session_id,
            )

        # 3) template from DB if possible
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

        # 4) LLM
        memory_context = self._get_memory_context(text)
        prompt = self._build_prompt(text, intent, memory_context)

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
            if hasattr(self.memory, "log_llm_call"):
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
                memory_used=bool(memory_context),
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
            memory_used=bool(memory_context),
        )

    # =========================
    # DIRECT REPLIES
    # =========================
    def _direct_reply(self, text, intent):
        t = self._normalize(text)

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
            # "Bana Tanem diyebilirsin"
            name = self._extract_user_name(text)
            if name:
                return f"Tamam. Sana {name} diyeyim."
            return "Tamam. Nasıl istersen öyle diyeyim."

        if intent == "ask_user_name":
            remembered = self._remembered_name()
            if remembered:
                return f"Senin adın {remembered}."
            return "Adını henüz bilmiyorum. Söylersen hatırlamaya çalışırım."

        if intent == "conversation_start":
            return "Tamam. Ne hakkında konuşalım?"

        if intent == "ask_question_back":
            return "Tabii. Bugün nasıl geçti?"

        if intent == "ask_topic":
            return "İstersen okul, oyunlar ya da arkadaşlar hakkında konuşabiliriz."

        if intent == "open_topic":
            return "Tamam. Başlayalım. İlk neyi konuşmak istersin?"

        return None

    # =========================
    # INTENT
    # =========================
    def detect_intent(self, text):
        t = self._normalize(text)

        if any(x in t for x in ["merhaba", "selam", "selamun aleykum", "selamün aleyküm"]):
            if "nasilsin" in t or "nasılsın" in text.lower():
                return "ask_status"
            return "greeting"

        if "senin adin ne" in t or "adın ne" in text.lower():
            return "ask_name"

        if "kimsin" in t or "kendini tanimlar misin" in t or "kendini tanımlar mısın" in text.lower():
            return "ask_identity"

        if "nasilsin" in t or "nasılsın" in text.lower() or "iyi misin" in t:
            return "ask_status"

        if "tesekkur" in t or "teşekkür" in text.lower():
            return "thanks"

        if "gorusuruz" in t or "görüşürüz" in text.lower() or "hosca kal" in t or "hoşça kal" in text.lower():
            return "farewell"

        if "bana " in t and " diyebilirsin" in t:
            return "user_name_define"

        if "benim adim nedir" in t or "benim adım nedir" in text.lower() or "adim ne" in t:
            return "ask_user_name"

        if "bana soru sor" in t:
            return "ask_question_back"

        if "ne konusalim" in t or "ne konuşalım" in text.lower():
            return "ask_topic"

        if "konusalim" in t or "konuşalım" in text.lower():
            return "conversation_start"

        return "general"

    # =========================
    # TEMPLATE ACCESS
    # =========================
    def _get_template(self, intent):
        if hasattr(self.memory, "get_template"):
            try:
                return self.memory.get_template(intent_name=intent)
            except TypeError:
                try:
                    return self.memory.get_template(intent)
                except Exception:
                    return None
            except Exception:
                return None
        return None

    # =========================
    # MEMORY
    # =========================
    def _remembered_name(self):
        if hasattr(self.memory, "get_person_by_role"):
            try:
                tanem = self.memory.get_person_by_role("tanem")
                if tanem and tanem.get("name"):
                    return tanem["name"]
            except Exception:
                pass
        return None

    def _extract_user_name(self, text):
        lowered = text.lower()
        marker = "bana "
        suffix = " diyebilirsin"

        if marker in lowered and suffix in lowered:
            start = lowered.find(marker) + len(marker)
            end = lowered.find(suffix)
            candidate = text[start:end].strip(" .,!?:;")
            if candidate:
                return candidate.title()
        return None

    def _get_memory_context(self, text):
        chunks = []

        remembered_name = self._remembered_name()
        if remembered_name:
            chunks.append(f"Kullanıcının adı {remembered_name}.")

        extracted = self._extract_user_name(text)
        if extracted:
            chunks.append(f"Kullanıcı kendisine {extracted} denmesini istedi.")

        if hasattr(self.memory, "search_memories"):
            try:
                memories = self.memory.search_memories(text, limit=3)
                if memories:
                    chunks.append("İlgili geçmiş bilgiler:")
                    for m in memories[:3]:
                        chunks.append(f"- {m}")
            except Exception:
                pass

        return "\n".join(chunks).strip()

    # =========================
    # PROMPT
    # =========================
    def _build_prompt(self, text, intent, memory_context):
        parts = [SYSTEM_PROMPT]

        if memory_context:
            parts.append("İlgili hafıza bilgileri:")
            parts.append(memory_context)

        parts.append(f"Intent: {intent}")
        parts.append(f"Kullanıcı: {text}")
        parts.append("Cevap:")

        return "\n\n".join(parts)

    # =========================
    # LOGGER
    # =========================
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
            if hasattr(self.memory, "log_conversation"):
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
            if hasattr(self.memory, "log_conversation_telemetry"):
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

    # =========================
    # NORMALIZE
    # =========================
    def _normalize(self, text):
        return (text or "").strip().lower()
