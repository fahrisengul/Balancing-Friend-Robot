from .intent_router import IntentRouter
from .dialogue_manager import DialogueManager
from .skill_handlers import SkillHandlers
from .response_policy import ResponsePolicy
from .llm_client import LLMClient
from .persona import build_system_prompt
from .models import BrainResult
from .education_engine import EducationEngine

from memory.memory_manager import MemoryManager
from memory.memory_writer import MemoryWriter
from memory.memory_retriever import MemoryRetriever


class PoodleBrain:
    def __init__(self):
        self.intent = IntentRouter()
        self.dialogue = DialogueManager()
        self.skills = SkillHandlers()
        self.policy = ResponsePolicy()
        self.llm = LLMClient()
        self.system_prompt = build_system_prompt()

        self.memory = MemoryManager()
        from datetime import date
        
        self.education = EducationEngine()
        self.writer = MemoryWriter(self.memory)
        self.retriever = MemoryRetriever(self.memory)

        self.template_first_intents = {
            "greeting",
            "farewell",
            "ask_name",
            "ask_identity",
            "ask_status",
            "thanks",
            "acknowledge",
            "followup",
            "followup_repair",
            "conversation_start",
            "ask_question_back",
            "ask_topic",
            "open_topic",
        }

        self.memory_worthy_intents = {
            "education_help",
            "study_planning",
            "homework_help",
            "exam_anxiety",
            "motivation_help",
            "focus_help",
            "request_advice",
            "emotional_support",
            "sadness_support",
            "frustration_support",
            "reassurance_request",
            "ask_user_profile",
            "share_preference",
            "statement",
            "question",
        }

    def handle_user_input(self, text: str) -> BrainResult:
        cleaned = (text or "").strip()
        context = self.dialogue.get_context()

        if not cleaned:
            reply = "Biraz daha açık söyler misin?"
            self.dialogue.update(cleaned, reply, "clarification_needed")
            return BrainResult(reply_text=reply, intent="clarification_needed")

        intent = self.intent.detect(cleaned, context)

        # -------------------------------------------------
        # Sprint 7 foundation: memory write
        # -------------------------------------------------
        if intent in self.memory_worthy_intents:
            try:
                self.writer.process(cleaned)
            except Exception as e:
                print(f">>> [MEMORY WRITER ERROR] {e}")

        # -------------------------------------------------
        # Sprint 6: education engine first
        # -------------------------------------------------
        try:
            education_reply = self.education.handle(cleaned, intent)
        except Exception as e:
            education_reply = None
            print(f">>> [EDUCATION ENGINE ERROR] {e}")

        if education_reply:
            followup = self._get_followup(intent)
            reply = self._merge_reply_and_followup(education_reply, followup)
            reply = self.policy.apply(reply)

            self.dialogue.update(cleaned, reply, intent)
            return BrainResult(reply_text=reply, intent=intent)

        # -------------------------------------------------
        # Deterministic direct replies
        # -------------------------------------------------
        shortcut = self._direct_reply(cleaned, intent)
        if shortcut:
            reply = self.policy.apply(shortcut)
            self.dialogue.update(cleaned, reply, intent)
            return BrainResult(reply_text=reply, intent=intent)

        # -------------------------------------------------
        # Template-first intents
        # -------------------------------------------------
        if intent in self.template_first_intents:
            reply = self._reply_from_template_or_fallback(intent, cleaned)
            reply = self.policy.apply(reply)

            self.dialogue.update(cleaned, reply, intent)
            return BrainResult(reply_text=reply, intent=intent)

        # -------------------------------------------------
        # Policy-driven path
        # -------------------------------------------------
        decision = self.policy.choose_source(cleaned, intent)

        if decision.source == "clarify":
            reply = decision.clarify_text or "Bunu biraz daha açık söyler misin?"
            self.dialogue.update(cleaned, reply, intent)
            return BrainResult(reply_text=reply, intent=intent)

        if decision.source == "skill":
            skill_result = self.skills.handle(intent, cleaned)
            if skill_result:
                reply = self.policy.apply(skill_result)
                self.dialogue.update(cleaned, reply, intent)
                return BrainResult(reply_text=reply, intent=intent)

        if decision.source == "template":
            reply = self._reply_from_template_or_fallback(intent, cleaned)
            reply = self.policy.apply(reply)

            self.dialogue.update(cleaned, reply, intent)
            return BrainResult(reply_text=reply, intent=intent)

        # -------------------------------------------------
        # Sprint 7 foundation: retrieval-aware LLM fallback
        # -------------------------------------------------
        try:
            memory_context = self.retriever.get_context(cleaned)
        except Exception as e:
            memory_context = ""
            print(f">>> [MEMORY RETRIEVER ERROR] {e}")

        prompt = self._build_prompt(cleaned, intent, memory_context)
        raw = self.llm.generate(prompt)
        answer = self.policy.apply(raw)

        if not answer or len(answer.strip()) < 2:
            answer = self._template_fallback(intent, cleaned)

        self.dialogue.update(cleaned, answer, intent)
        return BrainResult(reply_text=answer, intent=intent)

    # -------------------------------------------------
    # DIRECT REPLIES
    # -------------------------------------------------
    def _direct_reply(self, cleaned: str, intent: str):
        normalized = self._normalize(cleaned)

        if intent == "ask_status":
            if "her sey yolunda" in normalized or "her şey yolunda" in cleaned.lower():
                return "Evet, genel olarak yolunda. Sende durum nasıl?"
            if "iyi misin" in normalized:
                return "İyiyim. Sen nasılsın?"
            if "nasilsin" in normalized or "nasılsın" in cleaned.lower():
                return "İyiyim. Sen nasılsın?"

        if intent == "ask_user_profile":
            return "Şu an seni çok az tanıyorum. İstersen seni daha iyi tanıyabilirim."

        if intent == "conversation_start":
            return "Evet, isterim. Önce şunu sorayım: en çok ne yapmayı seversin?"

        if intent == "ask_question_back":
            return "Tabii. Bugün seni en çok ne mutlu etti?"

        if intent == "ask_topic":
            return "İstersen oyunlar, okul ya da arkadaşlar hakkında konuşabiliriz."

        if intent == "open_topic":
            return "Tamam. Bugün nasıl geçti?"

        return None

    # -------------------------------------------------
    # PROMPT
    # -------------------------------------------------
    def _build_prompt(self, cleaned: str, intent: str, memory_context: str = "") -> str:
        context_text = self.dialogue.get_recent_turns_as_text(limit=3)
        topic = self.dialogue.get_current_topic()

        tanem = self.memory.get_person_by_role("tanem")

        profile_block = ""
        if tanem:
            safe_bits = []

            name = tanem.get("name")
            grade = tanem.get("grade_level")
            school = tanem.get("school_name")

            if name:
                safe_bits.append(f"Adı: {name}")
            if grade:
                safe_bits.append(f"Sınıf: {grade}")
            if school:
                safe_bits.append(f"Okul: {school}")

            if safe_bits:
                profile_block = "Tanem hakkında ilgili bilgiler:\n- " + "\n- ".join(safe_bits)

        memory_block = memory_context.strip() if memory_context else "Yok"

        return f"""
{self.system_prompt}

{profile_block}

Hafıza:
{memory_block}

Son konuşma bağlamı:
{context_text}

Konu: {topic}
Intent: {intent}

Kullanıcı:
{cleaned}

Kurallar:
- Türkçe cevap ver.
- Kısa ve doğal konuş.
- Gereksiz giriş cümlesi kurma.
- Kullanıcının son cümlesine doğrudan cevap ver.
- Aynı cümleyi tekrar etme.
- Kullanıcı soru sorduysa önce soruya cevap ver.
- Eğitim ve kaygı konularında somut ve kısa öneriler ver.
- Çocuk dostu, sakin ve destekleyici ol.
- Eğitim cevaplarında en fazla 2-3 kısa cümle kullan.
- Hafızayı kullanırken doğal ol; ürkütücü veya aşırı detaylı konuşma.
""".strip()

    # -------------------------------------------------
    # TEMPLATE HELPERS
    # -------------------------------------------------
    def _reply_from_template_or_fallback(self, intent: str, text: str) -> str:
        template = self.memory.get_template(intent_name=intent)
        if template:
            return template

        followup = self._get_followup(intent)
        if followup:
            return followup

        return self._template_fallback(intent, text)

    def _get_followup(self, intent: str):
        getter = getattr(self.memory, "get_followup", None)
        if callable(getter):
            try:
                return getter(intent_name=intent)
            except TypeError:
                return getter(intent)
        return None

    def _merge_reply_and_followup(self, reply: str, followup: str):
        if not followup:
            return reply

        # Liste cevabıysa follow-up ekleme
        if "\n" in reply:
            return reply

        # Zaten uzunsa follow-up ekleme
        if len(reply.split()) > 22:
            return reply

        if reply.endswith((".", "!", "?")):
            return f"{reply} {followup}"
        return f"{reply}. {followup}"

    def _template_fallback(self, intent: str, text: str) -> str:
        if intent == "conversation_start":
            return "Seni tanımak isterim. En sevdiğin şey nedir?"

        if intent == "ask_question_back":
            return "Sana bir soru sorayım: bugün nasıldı?"

        if intent == "ask_topic":
            return "İstersen oyunlar, okul ya da arkadaşlar hakkında konuşabiliriz."

        if intent == "open_topic":
            return "Tamam. Bugün nasıl geçti?"

        if intent == "statement":
            return "Anladım. Devam etmek ister misin?"

        if intent == "farewell":
            return "Görüşürüz."

        if intent == "followup":
            return "Biraz daha anlatır mısın?"

        return "Bunu biraz daha açık söyler misin?"

    # -------------------------------------------------
    # NORMALIZE
    # -------------------------------------------------
    def _normalize(self, text: str) -> str:
        t = (text or "").lower().strip()
        t = (
            t.replace("ı", "i")
            .replace("ğ", "g")
            .replace("ş", "s")
            .replace("ç", "c")
            .replace("ö", "o")
            .replace("ü", "u")
        )
        return " ".join(t.split())
        
    def _run_daily_maintenance_if_needed(self):
    today = date.today().isoformat()

    # Basit local işaret dosyası
    marker_path = ".last_maintenance_date"

    last_run = None
    try:
        with open(marker_path, "r", encoding="utf-8") as f:
            last_run = f.read().strip()
    except FileNotFoundError:
        pass

    if last_run == today:
        return

    try:
        self.memory.rebuild_daily_metrics()
        self.memory.cleanup_logs(
            conversation_days=30,
            llm_days=90,
            system_event_days=60,
            run_vacuum=True,
        )

        with open(marker_path, "w", encoding="utf-8") as f:
            f.write(today)

        print(">>> [MAINTENANCE] Daily metrics + cleanup tamamlandı.")

    except Exception as e:
        print(f">>> [MAINTENANCE ERROR] {e}")

def _log_and_return(
    self,
    cleaned: str,
    intent: str,
    response_source: str,
    reply: str,
    session_id: str = None,
    model_name: str = None,
    latency_ms: int = None,
    memory_context_used: bool = False,
    status: str = "ok",
    error_text: str = None,
):
    normalized_text = self._normalize(cleaned)

    try:
        self.memory.log_conversation(
            raw_text=cleaned,
            normalized_text=normalized_text,
            intent=intent,
            response_source=response_source,
            reply_text=reply,
            session_id=session_id,
            model_name=model_name,
            latency_ms=latency_ms,
            memory_context_used=memory_context_used,
            status=status,
            error_text=error_text,
        )
    except Exception as e:
        print(f">>> [LOG CONVERSATION ERROR] {e}")

    self.dialogue.update(cleaned, reply, intent)
    return BrainResult(reply_text=reply, intent=intent)
