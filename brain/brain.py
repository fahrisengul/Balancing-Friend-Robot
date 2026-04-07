from .intent_router import IntentRouter
from .dialogue_manager import DialogueManager
from .skill_handlers import SkillHandlers
from .response_policy import ResponsePolicy
from .llm_client import LLMClient
from .persona import build_system_prompt
from .models import BrainResult
from memory.memory_manager import MemoryManager


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

        intent = self.intent.detect(cleaned)
        context = self.dialogue.get_context()
        decision = self.policy.choose_source(cleaned, intent)

        # --- CLARIFY ---
        if decision.source == "clarify":
            reply = decision.clarify_text or "Bunu tam anlayamadım. Bir kez daha söyler misin?"
            self.dialogue.update(cleaned, reply, intent)
            return BrainResult(reply_text=reply, intent=intent)

        # --- SKILL ---
        if decision.source == "skill":
            skill_result = self.skills.handle(intent, cleaned)
            if skill_result:
                self.dialogue.update(cleaned, skill_result, intent)
                return BrainResult(reply_text=skill_result, intent=intent)

        # --- TEMPLATE ---
        if decision.source == "template":
            template_reply = self.memory.get_template(intent)

            if template_reply:
                self.dialogue.update(cleaned, template_reply, intent)
                return BrainResult(reply_text=template_reply, intent=intent)

            fallback = self._handle_template_reply(intent, cleaned, context)
            self.dialogue.update(cleaned, fallback, intent)
            return BrainResult(reply_text=fallback, intent=intent)

        # --- LLM ---
        prompt = self._build_prompt(cleaned)
        raw = self.llm.generate(prompt)
        answer = self.policy.apply(raw)

        self.dialogue.update(cleaned, answer, intent)
        return BrainResult(reply_text=answer, intent=intent)

    # ---------------------------
    # PROMPT
    # ---------------------------
    def _build_prompt(self, cleaned: str) -> str:
        history_block = self.dialogue.get_recent_turns_as_text(limit=3)

        return f"""
{self.system_prompt}

Son konuşma:
{history_block}

Kullanıcı:
{cleaned}
""".strip()

    # ---------------------------
    # TEMPLATE FALLBACK
    # ---------------------------
    def _handle_template_reply(self, intent: str, text: str, context=None) -> str:
        t = (text or "").strip().lower()
        context = context or {}
        topic = context.get("current_topic")
        last_intent = context.get("last_intent")

        if intent == "greeting":
            return "Selam, ben Poodle."

        if intent == "ask_name":
            return "Benim adım Poodle."

        if intent == "ask_identity":
            return "Ben Poodle. Seninle konuşan robot arkadaşınım."

        if intent == "ask_status":
            return "İyiyim, teşekkür ederim. Sen nasılsın?"

        if intent == "thanks":
            return "Rica ederim."

        if intent == "acknowledge":
            return "Tamam."

        if intent == "smalltalk_short":
            return "Anladım."

        if intent == "followup":
            if topic == "school":
                return "Okulla ilgili kısmı biraz daha anlatır mısın?"

            if topic == "birthday":
                if last_intent in {"ask_birthdate", "ask_age"}:
                    return "Doğum günüyle ilgili neyi netleştirmek istediğini biraz daha açar mısın?"
                return "Doğum günüyle ilgili neyi merak ettiğini biraz daha açar mısın?"

            if topic == "emotion":
                return "Nasıl hissettiğini biraz daha anlatmak ister misin?"

            if topic == "education":
                return "Dersle ilgili hangi kısmı kastettiğini biraz daha açık söyler misin?"

            return "Bunu biraz daha açar mısın?"

        return "Bunu biraz daha açık söyler misin?"
