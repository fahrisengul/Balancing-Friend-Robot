import time
from datetime import date
from memory.memory_manager import MemoryManager


class PoodleBrain:

    def __init__(self, llm):
        self.llm = llm
        self.memory = MemoryManager()
        self._run_daily_maintenance_if_needed()

    # =========================
    # DAILY CLEANUP
    # =========================
    def _run_daily_maintenance_if_needed(self):
        marker = ".last_maintenance"

        try:
            with open(marker, "r") as f:
                last = f.read().strip()
        except:
            last = None

        today = date.today().isoformat()

        if last == today:
            return

        self.memory.cleanup_logs()
        self.memory.rebuild_daily_metrics()

        with open(marker, "w") as f:
            f.write(today)

        print(">>> [MAINTENANCE DONE]")

    # =========================
    # MAIN ENTRY
    # =========================
    def handle(self, text):

        intent = self.detect_intent(text)

        # TEMPLATE / SKILL vs LLM
        if intent == "greeting":
            return self._log_and_return(text, intent, "template", "Selam.")

        # =========================
        # LLM FLOW
        # =========================
        prompt = f"Kullanıcı: {text}"

        start = time.perf_counter()
        error = None
        raw = None

        try:
            raw = self.llm.generate(prompt)
        except Exception as e:
            error = str(e)

        latency = int((time.perf_counter() - start) * 1000)

        model = getattr(self.llm, "model_name", "unknown")

        # LLM LOG
        self.memory.log_llm_call(
            model_name=model,
            intent=intent,
            prompt_chars=len(prompt),
            response_chars=len(raw) if raw else 0,
            latency_ms=latency,
            status="error" if error else "ok",
            error_text=error
        )

        if error:
            return self._log_and_return(
                text, intent, "llm",
                "Şu an bir sorun var.",
                model, latency, False, "error", error
            )

        return self._log_and_return(
            text, intent, "llm",
            raw,
            model, latency, False
        )

    # =========================
    # LOGGER WRAPPER
    # =========================
    def _log_and_return(
        self,
        text,
        intent,
        source,
        reply,
        model=None,
        latency=None,
        memory_used=False,
        status="ok",
        error=None
    ):

        self.memory.log_conversation(
            raw_text=text,
            normalized_text=text.lower(),
            intent=intent,
            response_source=source,
            reply_text=reply,
            model_name=model,
            latency_ms=latency,
            memory_context_used=memory_used,
            status=status,
            error_text=error
        )

        return reply

    # =========================
    # INTENT (placeholder)
    # =========================
    def detect_intent(self, text):
        if "selam" in text.lower():
            return "greeting"
        return "general"
