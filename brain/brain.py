import time
from datetime import date
from typing import Optional, Dict, Any

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
- Sorulan soruya doğrudan cevap ver.
- Gereksiz tekrar yapma.
- Cevapların pratik değer taşısın.
""".strip()


EDUCATION_PROMPT = """
Bu konuşma eğitim modundadır.

Kurallar:
- Öğrenci seviyesinde açık ve öğretici anlat.
- Gerekirse detay ver ama konu dışına çıkma.
- Konu soruluyorsa önce tanımı ver, sonra kısa açıklama yap.
- Uygunsa küçük örnek ver.
- Strateji soruluyorsa uygulanabilir öneriler sun.
- Bağlamdaki bilgileri öncelikli kullan.
- Bağlam yetersizse dürüstçe güvenli bir çerçeve sun.
""".strip()


GENERAL_PROMPT = """
Bu konuşma genel moddadır.

Kurallar:
- Doğal konuş.
- Kısa sorulara yüzeysel değil, anlamlı cevap ver.
- Gereksiz rol oyunu yapma.
- Konu açıksa biraz açıklayıcı ol.
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

        self.last_turn: Dict[str, Any] = {
            "raw_text": "",
            "resolved_text": "",
            "intent": None,
            "mode": None,
            "topic_hint": None,
            "reply": "",
        }

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

        self._safe_memory_write(text)

        resolved = self._resolve_follow_up(text)
        effective_text = resolved["effective_text"]

        intent = self.detect_intent(effective_text)
        mode = self._detect_mode(effective_text, intent)

        fast = self._try_fast_track(effective_text, intent, mode)
        if fast:
            self._remember_turn(
                raw_text=text,
                resolved_text=effective_text,
                intent=intent,
                mode=mode,
                reply=fast,
            )
            return self._log_and_return(
                text=text,
                intent=intent,
                source="fast_track",
                reply=fast,
                session_id=session_id,
            )

        direct = self._direct_reply(effective_text, intent)
        if direct:
            self._remember_turn(
                raw_text=text,
                resolved_text=effective_text,
                intent=intent,
                mode=mode,
                reply=direct,
            )
            return self._log_and_return(
                text=text,
                intent=intent,
                source="direct",
                reply=direct,
                session_id=session_id,
            )

        template = self._get_template(intent)
        if template and intent in {"ask_identity", "ask_name", "ask_user_name", "user_name_define"}:
            self._remember_turn(
                raw_text=text,
                resolved_text=effective_text,
                intent=intent,
                mode=mode,
                reply=template,
            )
            return self._log_and_return(
                text=text,
                intent=intent,
                source="template",
                reply=template,
                session_id=session_id,
            )

        if self._should_clarify(effective_text, intent):
            reply = "Son kısmı tam anlayamadım. Bir kez daha söyler misin?"
            self._remember_turn(
                raw_text=text,
                resolved_text=effective_text,
                intent=intent,
                mode=mode,
                reply=reply,
            )
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
        confidence = float(bundle["confidence"])
        memory_used = bool(context.strip())

        llm_mode = self._select_llm_mode(intent=intent, mode=mode, confidence=confidence)

        prompt = self._build_prompt(
            text=effective_text,
            intent=intent,
            mode=mode,
            context=context,
            confidence=confidence,
            is_follow_up=resolved["is_follow_up"],
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
            self._remember_turn(
                raw_text=text,
                resolved_text=effective_text,
                intent=intent,
                mode=mode,
                reply=reply,
            )
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
        if not reply:
            reply = "Bunu bir kez daha söyler misin?"

        self._remember_turn(
            raw_text=text,
            resolved_text=effective_text,
            intent=intent,
            mode=mode,
            reply=reply,
        )
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

    # =========================================================
    # FOLLOW-UP
    # =========================================================
    def _resolve_follow_up(self, text: str) -> Dict[str, Any]:
        raw = (text or "").strip()
        norm = self._normalize(raw)

        follow_up_markers = [
            "bir de",
            "daha fazla",
            "detay ver",
            "biraz daha",
            "bunu aç",
            "onu aç",
            "örnek ver",
            "başka ne",
            "devam et",
            "onu tekrar",
        ]

        is_follow_up = any(marker in norm for marker in follow_up_markers)

        if not is_follow_up:
            return {
                "is_follow_up": False,
                "effective_text": raw,
            }

        prev_topic = self.last_turn.get("resolved_text") or ""
        prev_intent = self.last_turn.get("intent") or "general"

        if prev_topic:
            effective = f"Önceki konu: {prev_topic}. Yeni istek: {raw}"
        else:
            effective = raw

        # follow-up ise intent'i daha iyi koru
        if prev_intent in {"concept_explanation", "exam_support", "education_topics"}:
            return {
                "is_follow_up": True,
                "effective_text": effective,
            }

        return {
            "is_follow_up": True,
            "effective_text": effective,
        }

    # =========================================================
    # INTERNAL FLOW
    # =========================================================
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
        }

    def _select_llm_mode(self, intent: str, mode: str, confidence: float) -> str:
        if intent in {"ask_name", "ask_identity", "audio_check", "thanks", "greeting", "farewell"}:
            return "deterministic"

        if intent in {"concept_explanation", "exam_support", "follow_up"}:
            return "deep"

        if intent == "education_topics":
            return "balanced"

        if confidence >= 0.70:
            return "deep"

        if confidence >= 0.45:
            return "balanced"

        return "balanced"

    def _build_prompt(
        self,
        text: str,
        intent: str,
        mode: str,
        context: str,
        confidence: float,
        is_follow_up: bool,
    ) -> str:
        parts = [SYSTEM_PROMPT]

        if mode == "education":
            parts.append(EDUCATION_PROMPT)
        else:
            parts.append(GENERAL_PROMPT)

        parts.append(self._depth_instruction(intent=intent, mode=mode, confidence=confidence, is_follow_up=is_follow_up))

        if context:
            parts.append("Bağlam:")
            parts.append(context)
        else:
            parts.append("Bağlam: Kullanılabilir ek bağlam bulunamadı. Güvenli ve dürüst kal.")

        parts.append(f"Soru: {text}")
        parts.append("Cevap:")

        return "\n\n".join(parts).strip()

    def _depth_instruction(self, intent: str, mode: str, confidence: float, is_follow_up: bool) -> str:
        if is_follow_up:
            return (
                "Yanıt biçimi: Bu bir devam sorusu. Önceki bağlamı koru, aynı konuyu sürdür, "
                "gerekirse biraz daha detay ver."
            )

        if mode == "education":
            if intent == "education_topics":
                return (
                    "Yanıt biçimi: İlgili konu başlıklarını düzenli ver. "
                    "Gerekirse kısa açıklama ekle. "
                    "Bağlam güçlüyse biraz detaylandır."
                )

            if intent == "exam_support":
                return (
                    "Yanıt biçimi: Önce kısa çerçeve ver, sonra 2-4 uygulanabilir öneri sun. "
                    "Bağlam güçlüyse biraz derinleş."
                )

            if intent == "concept_explanation":
                return (
                    "Yanıt biçimi: Önce tanımı ver, sonra sade açıklama yap, ardından kısa örnek ver. "
                    "Bağlam güçlüyse biraz ayrıntı ekle."
                )

        if confidence >= 0.75:
            return "Yanıt biçimi: Bağlam güçlü. Daha değerli ve açıklayıcı cevap ver, ama konu dışına çıkma."
        if confidence >= 0.45:
            return "Yanıt biçimi: Orta derinlikte, sade ve faydalı cevap ver."
        return "Yanıt biçimi: Kısa ama anlamlı ve dürüst cevap ver."

    def _try_fast_track(self, text: str, intent: str, mode: str) -> Optional[str]:
        hard_intents = {"greeting", "ask_name", "ask_identity", "audio_check", "thanks", "farewell", "ask_status"}

        if intent in hard_intents:
            answer = self.memory.search_fast_answer(text, intent=intent)
            if answer:
                return answer

        if mode == "education" and intent == "education_topics":
            answer = self.memory.search_fast_answer(text, intent=intent)
            if answer:
                return answer

        return None

    def _direct_reply(self, text: str, intent: str) -> Optional[str]:
        if intent == "conversation_start":
            return "Tamam. Ne hakkında konuşalım?"
        return None

    # =========================================================
    # INTENT / MODE
    # =========================================================
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
            "lgs" in t or "dgs" in t
        ) and (
            "konu" in t or "list" in t or "odaklan" in t
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
            or ("lgs" in t and "bilgi" in t)
        ):
            return "exam_support"

        if (
            "nedir" in t
            or "anlatir misin" in t
            or "anlatır mısın" in raw
            or "detay verir misin" in raw
            or "bilgi verir misin" in raw
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
