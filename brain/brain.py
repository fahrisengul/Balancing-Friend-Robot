import time
from datetime import date

from memory.memory_manager import MemoryManager
from .models import BrainResult


class PoodleBrain:

    def __init__(self, llm):
        self.llm = llm
        self.memory = MemoryManager()
        self._run_daily_maintenance_if_needed()

    # =========================
    # DAILY MAINTENANCE
    # =========================
    def _run_daily_maintenance_if_needed(self):
        marker = ".last_maintenance"

        try:
            with open(marker, "r", encoding="utf-8") as f:
                last = f.read().strip()
        except:
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

    # =========================
    # ORCHESTRATOR API
    # =========================
    def handle_user_input(self, text, session_id=None):
        return self.handle(text, session_id)

    # =========================
    # MAIN LOGIC
    # =========================
    def handle(self, text, session_id=None):

        text = (text or "").strip()

        if not text:
            return self._log_and_return(
                text="",
                intent="empty",
                source="clarify",
                reply="Biraz daha açık söyler misin?",
                session_id=session_id
            )

        intent = self.detect_intent(text)

        # ---- TEMPLATE ----
        if intent == "greeting":
            return self._log_and_return(
                text=text,
                intent=intent,
                source="template",
                reply="Selam.",
                session_id=session_id
            )

        # ---- LLM FLOW ----
        prompt = f"Kullanıcı: {text}"

        start = time.perf_counter()
        raw = None
        error = None

        try:
            raw = self.llm.generate(prompt)
        except Exception as e:
            error = str(e)

        latency = int((time.perf_counter() - start) * 1000)

        model = getattr(self.llm, "model_name", None) or getattr(self.llm, "model", "unknown")

        # LLM LOG
        try:
            self.memory.log_llm_call(
                session_id=session_id,
                intent=intent,
                model_name=model,
                prompt_chars=len(prompt),
                response_chars=len(raw) if raw else 0,
                latency_ms=latency,
                status="error" if error else "ok",
                error_text=error
            )
        except Exception as e:
            print(f">>> [LOG LLM ERROR] {e}")

        if error:
            return self._log_and_return(
                text=text,
                intent=intent,
                source="llm",
                reply="Şu an bir sorun var.",
                session_id=session_id,
                model=model,
                latency=latency,
                status="error",
                error=error
            )

        final_reply = raw if raw else "Bir şeyler ters gitti."

        return self._log_and_return(
            text=text,
            intent=intent,
            source="llm",
            reply=final_reply,
            session_id=session_id,
            model=model,
            latency=latency
        )

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
        error=None
    ):

        normalized = self._normalize(text)

        # conversation_logs
        try:
            self.memory.log_conversation(
                raw_text=text,
                normalized_text=normalized,
                intent=intent,
                response_source=source,
                reply_text=reply
            )
        except Exception as e:
            print(f">>> [LOG CONVERSATION ERROR] {e}")

        # telemetry
        try:
            self.memory.log_conversation_telemetry(
                session_id=session_id,
                intent=intent,
                response_source=source,
                model_name=model,
                latency_ms=latency,
                memory_context_used=memory_used,
                status=status,
                error_text=error
            )
        except Exception as e:
            print(f">>> [LOG TELEMETRY ERROR] {e}")

        return BrainResult(reply_text=reply, intent=intent)

    # =========================
    # INTENT (TEMP)
    # =========================
    def detect_intent(self, text):

        t = text.lower()

        if "merhaba" in t or "selam" in t:
            return "greeting"

        return "general"

    # =========================
    # NORMALIZE
    # =========================
    def _normalize(self, text):
        return (text or "").strip().lower()
