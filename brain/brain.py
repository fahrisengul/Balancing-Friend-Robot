from .intent_router import IntentRouter
from .dialogue_manager import DialogueManager
from .skill_handlers import SkillHandlers
from .response_policy import ResponsePolicy
from .llm_client import LLMClient
from .persona import build_system_prompt
from .models import BrainResult
from memory.memory_manager import MemoryManager
from .education_engine import EducationEngine

class PoodleBrain:
    def __init__(self):
        self.intent = IntentRouter()
        self.dialogue = DialogueManager()
        self.skills = SkillHandlers()
        self.policy = ResponsePolicy()
        self.llm = LLMClient()
        self.system_prompt = build_system_prompt()
        self.memory = MemoryManager()
        self.education = EducationEngine()

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

    def handle_user_input(self, text: str) -> BrainResult:
        cleaned = (text or "").strip()
        context = self.dialogue.get_context()

        intent = self.intent.detect(cleaned, context)
        
        education_reply = self.education.handle(cleaned, intent)
        if education_reply:
            self.dialogue.update(cleaned, education_reply, intent)
            return BrainResult(reply_text=education_reply, intent=intent)

        # -----------------------------------
        # Önce deterministic shortcut
        # -----------------------------------
        shortcut = self._direct_reply(cleaned, intent)
        if shortcut:
            self.dialogue.update(cleaned, shortcut, intent)
            return BrainResult(reply_text=shortcut, intent=intent)

        # -----------------------------------
        # Template-first intentler
        # -----------------------------------
        if intent in self.template_first_intents:
            reply = self._reply_from_template_or_fallback(intent, cleaned)
            self.dialogue.update(cleaned, reply, intent)
            return BrainResult(reply_text=reply, intent=intent)

        # -----------------------------------
        # Policy
        # -----------------------------------
        decision = self.policy.choose_source(cleaned, intent)

        if decision.source == "clarify":
            reply = decision.clarify_text or "Bunu biraz daha açık söyler misin?"
            self.dialogue.update(cleaned, reply, intent)
            return BrainResult(reply_text=reply, intent=intent)

        if decision.source == "skill":
            skill_result = self.skills.handle(intent, cleaned)
            if skill_result:
                self.dialogue.update(cleaned, skill_result, intent)
                return BrainResult(reply_text=skill_result, intent=intent)

        if decision.source == "template":
            reply = self._reply_from_template_or_fallback(intent, cleaned)
            self.dialogue.update(cleaned, reply, intent)
            return BrainResult(reply_text=reply, intent=intent)

        # -----------------------------------
        # LLM
        # -----------------------------------
        prompt = self._build_prompt(cleaned, intent)
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
                return "Evet, şimdilik yolunda görünüyor. Sende durum nasıl?"
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

        if intent == "exam_anxiety":
            return "Bu his çok normal. İstersen önce seni en çok geren kısmı bulalım."

        if intent == "request_advice":
            if "5" in normalized or "bes" in normalized:
                return (
                    "1. Derin nefes al.\n"
                    "2. Kısa bir mola ver.\n"
                    "3. Yapacağın şeyi küçük parçalara böl.\n"
                    "4. Önce kolay yerden başla.\n"
                    "5. Kendine sert davranma."
                )
            return "İstersen buna uygun birkaç kısa öneri söyleyebilirim."

        return None

    # -------------------------------------------------
    # PROMPT
    # -------------------------------------------------
    def _build_prompt(self, cleaned: str, intent: str) -> str:
        context_text = self.dialogue.get_recent_turns_as_text(limit=3)
        topic = self.dialogue.get_current_topic()

        tanem = self.memory.get_person_by_role("tanem")

        memory_block = ""
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
                memory_block = "Tanem hakkında ilgili bilgiler:\n- " + "\n- ".join(safe_bits)

        return f"""
{self.system_prompt}

{memory_block}

Bağlam:
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
- Eğitim ve endişe konularında somut öneri ver.
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
            return getter(intent_name=intent)
        return None

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
