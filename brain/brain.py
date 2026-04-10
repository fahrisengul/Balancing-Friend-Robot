from .intent_router import IntentRouter
from .dialogue_manager import DialogueManager
from .skill_handlers import SkillHandlers
from .response_policy import ResponsePolicy
from .llm_client import LLMClient
from .persona import build_system_prompt
from .models import BrainResult
from memory.memory_manager import MemoryManager

import random


class PoodleBrain:
    def __init__(self):
        self.intent = IntentRouter()
        self.dialogue = DialogueManager()
        self.skills = SkillHandlers()
        self.policy = ResponsePolicy()
        self.llm = LLMClient()
        self.system_prompt = build_system_prompt()
        self.memory = MemoryManager()

    def handle_user_input(self, text: str) -> BrainResult:
        cleaned = (text or "").strip()
        context = self.dialogue.get_context()

        intent = self.intent.detect(cleaned, context)
        decision = self.policy.choose_source(cleaned, intent)

        # -----------------------------------
        # CLARIFY
        # -----------------------------------
        if decision.source == "clarify":
            reply = decision.clarify_text or "Bunu biraz daha açık söyler misin?"
            self.dialogue.update(cleaned, reply, intent)
            return BrainResult(reply_text=reply, intent=intent)

        # -----------------------------------
        # SKILL
        # -----------------------------------
        if decision.source == "skill":
            skill_result = self.skills.handle(intent, cleaned)
            if skill_result:
                self.dialogue.update(cleaned, skill_result, intent)
                return BrainResult(reply_text=skill_result, intent=intent)
            decision.source = "llm"

        # -----------------------------------
        # TEMPLATE
        # -----------------------------------
        if decision.source == "template":
            template = self.memory.get_template(intent_name=intent)

            if template:
                # 🎯 varyasyon
                reply = random.choice(template) if isinstance(template, list) else template
                self.dialogue.update(cleaned, reply, intent)
                return BrainResult(reply_text=reply, intent=intent)

            # fallback
            reply = self._template_fallback(intent, cleaned)
            self.dialogue.update(cleaned, reply, intent)
            return BrainResult(reply_text=reply, intent=intent)

        # -----------------------------------
        # LLM
        # -----------------------------------
        prompt = self._build_prompt(cleaned)
        raw = self.llm.generate(prompt)
        answer = self.policy.apply(raw)

        self.dialogue.update(cleaned, answer, intent)
        return BrainResult(reply_text=answer, intent=intent)

    # -------------------------------------------------
    # PROMPT
    # -------------------------------------------------
    def _build_prompt(self, cleaned: str) -> str:
        context_text = self.dialogue.get_recent_turns_as_text()
        topic = self.dialogue.get_current_topic()

        tanem = self.memory.get_person_by_role("tanem")

        memory_block = ""
        if tanem:
            memory_block = f"Tanem hakkında: {tanem}"

        return f"""
{self.system_prompt}

{memory_block}

Bağlam:
{context_text}

Konu: {topic}

Kullanıcı:
{cleaned}
""".strip()

    # -------------------------------------------------
    # TEMPLATE FALLBACK (SMART)
    # -------------------------------------------------
    def _template_fallback(self, intent: str, text: str) -> str:
        t = (text or "").lower()

        if intent == "conversation_start":
            return "Seni tanımak isterim. Bana biraz kendinden bahseder misin?"

        if intent == "ask_question_back":
            return "Sana bir soru sorayım: bugün seni en çok ne zorladı?"

        if intent == "ask_topic":
            return "İstersen oyunlar, okul ya da arkadaşlar hakkında konuşabiliriz."

        if intent == "open_topic":
            return "Bugün okulda nasıldı? İlginç bir şey oldu mu?"

        if intent == "statement":
            return "Anladım. Devam etmek ister misin?"

        if intent == "farewell":
            return "Görüşürüz."

        return "Anladım."
