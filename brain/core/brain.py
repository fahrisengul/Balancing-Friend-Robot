import json
import time
from datetime import date
from typing import Dict, Any

from memory.processing.memory_manager import MemoryManager
from memory.processing.memory_writer import MemoryWriter
from memory.retrieval.memory_retriever import MemoryRetriever
from memory.retrieval.faiss_adapter import FaissAdapter

from ..models import BrainResult
from ..response.response_policy import ResponsePolicy
from ..intent.intent_router import IntentRouter
from ..prompt.prompt_builder import PromptBuilder
from ..response.output_validator import OutputValidator
from ..response.response_selector import ResponseSelector

try:
    from ..llm_client import LLMClient
except Exception:
    LLMClient = None


class PoodleBrain:
    def __init__(self, llm=None):
        if llm is None:
            if LLMClient is None:
                raise RuntimeError("LLMClient import edilemedi ve dışarıdan llm verilmedi.")
            llm = LLMClient()

        self.llm = llm
        self.memory = MemoryManager()
        self.faiss = FaissAdapter()
        self.writer = MemoryWriter(self.memory)
        self.retriever = MemoryRetriever(self.memory, self.faiss)
        self.policy = ResponsePolicy()
        self._run_daily_maintenance_if_needed()

        self.last_turn: Dict[str, Any] = {
            "raw_text": "",
            "resolved_text": "",
            "intent": None,
            "mode": None,
            "topic_hint": None,
            "reply": "",
            "reply_summary": "",
        }

    def ask_poodle(self, text: str, session_id=None) -> str:
        result = self.handle(text, session_id=session_id)
        if isinstance(result, BrainResult):
            return result.reply_text
        return str(result)

    def ask_poodle_stream(self, text: str, session_id=None):
        result = self.handle(text, session_id=session_id)
        reply = result.reply_text if isinstance(result, BrainResult) else str(result)
        yield {"type": "final", "text": reply}
        yield {"type": "done", "text": reply}

    def handle_user_input(self, text, session_id=None):
        return self.handle(text, session_id=session_id)

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

        self._safe_memory_write(text)

        resolved = self._resolve_follow_up(text)
        effective_text = resolved["effective_text"]

        intent = IntentRouter.detect_intent(effective_text)
        mode = IntentRouter.detect_mode(effective_text, intent)

        guarded = IntentRouter.intent_guard(text=text, intent=intent)
        if guarded:
            self._remember_turn(text, effective_text, intent, mode, guarded)
            return self._log_and_return(
                text=text,
                intent=intent,
                source="guard",
                reply=guarded,
                session_id=session_id,
            )

        fast = ResponseSelector.try_fast_track(self.memory, effective_text, intent, mode)
        if fast:
            self._remember_turn(text, effective_text, intent, mode, fast)
            return self._log_and_return(
                text=text,
                intent=intent,
                source="fast_track",
                reply=fast,
                session_id=session_id,
            )

        direct = ResponseSelector.direct_reply(effective_text, intent)
        if direct:
            self._remember_turn(text, effective_text, intent, mode, direct)
            return self._log_and_return(
                text=text,
                intent=intent,
                source="direct",
                reply=direct,
                session_id=session_id,
            )

        template = ResponseSelector.get_template(self.memory, intent)
        if template and intent in {
            "ask_identity",
            "ask_name",
            "ask_user_name",
            "user_name_define",
            "thanks",
            "farewell",
            "greeting",
            "ask_status",
        }:
            self._remember_turn(text, effective_text, intent, mode, template)
            return self._log_and_return(
                text=text,
                intent=intent,
                source="template",
                reply=template,
                session_id=session_id,
            )

        if IntentRouter.should_clarify(effective_text, intent):
            reply = "Son kısmı tam anlayamadım. Bir kez daha söyler misin?"
            self._remember_turn(text, effective_text, intent, mode, reply)
            return self._log_and_return(
                text=text,
                intent=intent,
                source="clarify",
                reply=reply,
                session_id=session_id,
            )

        bundle = self.retriever.get_context_bundle(
            text=effective_text,
            intent=intent,
            mode=mode,
            top_k=5,
        )

        context = bundle["context_text"]
        selected_chunks = bundle.get("selected_chunks", [])
        confidence = float(bundle["confidence"])
        retrieval_source = bundle.get("source", "none")
        memory_used = bool(context.strip())
        query_variants = bundle.get("query_variants", [])
        reranked_preview = bundle.get("reranked_preview", [])

        llm_mode = ResponseSelector.select_llm_mode(
            intent=intent,
            mode=mode,
            confidence=confidence,
            selected_chunks=selected_chunks,
        )

        try:
            self.memory.log_retrieval_debug(
                session_id=session_id,
                intent=intent,
                mode=mode,
                query_text=effective_text,
                query_variants_json=json.dumps(query_variants, ensure_ascii=False),
                selected_chunks_json=json.dumps(reranked_preview, ensure_ascii=False),
                confidence=confidence,
                retrieval_source=retrieval_source,
                context_chars=len(context or ""),
            )
        except Exception as e:
            print(f">>> [LOG RETRIEVAL ERROR] {e}")

        prompt = PromptBuilder.build_prompt_v2(
            text=effective_text,
            intent=intent,
            mode=mode,
            confidence=confidence,
            retrieval_source=retrieval_source,
            selected_chunks=selected_chunks,
            context=context,
            is_follow_up=resolved["is_follow_up"],
            last_turn=self.last_turn,
        )

        start = time.perf_counter()
        raw = None
        error = None

        try:
            raw = self.llm.generate(prompt, mode=llm_mode)
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
            reply = "Şu an cevap verirken küçük bir sorun oldu."
            self._remember_turn(text, effective_text, intent, mode, reply)
            return self._log_and_return(
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

        reply = self.policy.apply(raw)
        reply = OutputValidator.validate_llm_output(
            reply=reply,
            intent=intent,
            mode=mode,
            confidence=confidence,
        )

        if not reply:
            reply = "Bunu bir kez daha söyler misin?"

        self._remember_turn(text, effective_text, intent, mode, reply)
        self._push_short_term_memory(effective_text, intent, mode, reply)

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

    def _resolve_follow_up(self, text: str) -> Dict[str, Any]:
        raw = (text or "").strip()
        norm = self._normalize(raw)

        follow_up_markers = [
            "bir de", "daha fazla", "detay ver", "biraz daha",
            "bunu aç", "onu aç", "örnek ver", "başka ne",
            "devam et", "onu tekrar", "biraz aç", "daha detaylı",
            "peki ya",
        ]

        is_follow_up = any(marker in norm for marker in follow_up_markers)

        if not is_follow_up:
            return {"is_follow_up": False, "effective_text": raw}

        prev_topic = self.last_turn.get("resolved_text") or ""
        prev_reply = self.last_turn.get("reply_summary") or ""

        if prev_topic:
            effective = (
                f"Önceki kullanıcı konusu: {prev_topic}. "
                f"Önceki yanıt özeti: {prev_reply}. "
                f"Yeni istek: {raw}"
            )
        else:
            effective = raw

        return {"is_follow_up": True, "effective_text": effective}

    def _safe_memory_write(self, text: str):
        try:
            self.writer.process(text)
        except Exception as e:
            print(f">>> [MEMORY WRITER ERROR] {e}")

    def _push_short_term_memory(self, text: str, intent: str, mode: str, reply: str):
        try:
            items = [
                {
                    "id": f"short.user.{hash(text)}",
                    "subject": "Conversation",
                    "topic": intent,
                    "chunk_type": "simple_explanation",
                    "title": "Kullanıcı son mesajı",
                    "content": text,
                    "keywords": [],
                    "difficulty": "easy",
                    "audience": "assistant",
                    "intent_tags": [intent, mode],
                    "embedding_priority": 0.90,
                },
                {
                    "id": f"short.reply.{hash(reply)}",
                    "subject": "Conversation",
                    "topic": intent,
                    "chunk_type": "simple_explanation",
                    "title": "Asistan son cevabı",
                    "content": reply,
                    "keywords": [],
                    "difficulty": "easy",
                    "audience": "assistant",
                    "intent_tags": [intent, mode, "reply"],
                    "embedding_priority": 0.85,
                },
            ]
            self.faiss.add_short_term(items)
        except Exception as e:
            print(f">>> [SHORT TERM FAISS ERROR] {e}")

    def _remember_turn(self, raw_text: str, resolved_text: str, intent: str, mode: str, reply: str):
        self.last_turn = {
            "raw_text": raw_text,
            "resolved_text": resolved_text,
            "intent": intent,
            "mode": mode,
            "reply": reply,
            "reply_summary": reply[:220],
        }

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
        return IntentRouter.normalize(text)
