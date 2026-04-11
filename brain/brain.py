import time
from datetime import date
from memory.memory_manager import MemoryManager


class PoodleBrain:
    def __init__(self, llm):
        self.llm = llm
        self.memory = MemoryManager()
        self._run_daily_maintenance_if_needed()

    # =========================
    # DAILY CLEANUP / METRICS
    # MacBook'ta uygulama açıldığında günde bir kez çalışır
    # Pi tarafında bunu cron'a taşıyacağız
    # =========================
    def _run_daily_maintenance_if_needed(self):
        marker = ".last_maintenance"

        try:
            with open(marker, "r", encoding="utf-8") as f:
                last = f.read().strip()
        except FileNotFoundError:
            last = None
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

    # =========================
    # MAIN ENTRY
    # =========================
    def handle(self, text, session_id=None):
        text = (text or "").strip()
        if not text:
            return self._log_and_return(
                text="",
                intent="empty",
                source="clarify",
                reply="Biraz daha açık söyler misin?",
                session_id=session_id,
                status="ok",
            )

        intent = self.detect_intent(text)

        # ---------------------------------
        # TEMPLATE / SKILL kısa yol
        # ---------------------------------
        if intent == "greeting":
            return self._log_and_return(
                text=text,
                intent=intent,
                source="template",
                reply="Selam.",
                session_id=session_id,
                status="ok",
            )

        # ---------------------------------
        # LLM FLOW
        # ---------------------------------
        prompt = f"Kullanıcı: {text}"

        start = time.perf_counter()
        error = None
        raw = None

        try:
            raw = self.llm.generate(prompt)
        except Exception as e:
            error = str(e)

        latency = int((time.perf_counter() - start) * 1000)

        model = getattr(self.llm, "model_name", None)
        if not model:
            model = getattr(self.llm, "model", "unknown")

        # LLM telemetry
        try:
            self.memory.log_llm_call(
                session_id=session_id,
                model_name=model,
                intent=intent,
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
                reply="Şu an bir sorun var.",
                session_id=session_id,
                model=model,
                latency=latency,
                memory_used=False,
                status="error",
                error=error,
            )

        final_reply = raw if raw else "Bir şeyler ters gitti."

        return self._log_and_return(
            text=text,
            intent=intent,
            source="llm",
            reply=final_reply,
            session_id=session_id,
            model=model,
            latency=latency,
            memory_used=False,
            status="ok",
        )

    # =========================
    # LOGGER WRAPPER
    # conversation_logs + conversation_telemetry birlikte yazılır
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

        # 1) Eski conversation log
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

        # 2) Yeni telemetry log
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

        return reply

    # =========================
    # INTENT (placeholder)
    # Burayı kendi gerçek intent_router yapına bağlayacaksın
    # =========================
    def detect_intent(self, text):
        lower = text.lower()

        if "selam" in lower or "merhaba" in lower:
            return "greeting"

        return "general"

    # =========================
    # NORMALIZER
    # =========================
    def _normalize(self, text):
        return (text or "").strip().lower()

def handle_user_input(self, text, session_id=None):
    text = (text or "").strip()
    if not text:
        return self._log_and_return(
            text="",
            intent="empty",
            source="clarify",
            reply="Biraz daha açık söyler misin?",
            session_id=session_id,
            status="ok",
        )

    intent = self.detect_intent(text)

    if intent == "greeting":
        return self._log_and_return(
            text=text,
            intent=intent,
            source="template",
            reply="Selam.",
            session_id=session_id,
            status="ok",
        )

    prompt = f"Kullanıcı: {text}"

    start = time.perf_counter()
    error = None
    raw = None

    try:
        raw = self.llm.generate(prompt)
    except Exception as e:
        error = str(e)

    latency = int((time.perf_counter() - start) * 1000)

    model = getattr(self.llm, "model_name", None)
    if not model:
        model = getattr(self.llm, "model", "unknown")

    try:
        self.memory.log_llm_call(
            session_id=session_id,
            model_name=model,
            intent=intent,
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
            reply="Şu an bir sorun var.",
            session_id=session_id,
            model=model,
            latency=latency,
            memory_used=False,
            status="error",
            error=error,
        )

    final_reply = raw if raw else "Bir şeyler ters gitti."

    return self._log_and_return(
        text=text,
        intent=intent,
        source="llm",
        reply=final_reply,
        session_id=session_id,
        model=model,
        latency=latency,
        memory_used=False,
        status="ok",
    )


def handle(self, text, session_id=None):
    return self.handle_user_input(text, session_id=session_id)
