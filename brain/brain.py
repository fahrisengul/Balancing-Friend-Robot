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

        # 1) intent tespit et
        intent = self.intent.detect(cleaned)

        # 2) response kaynağını seç
        decision = self.policy.choose_source(cleaned, intent)

        # 3) clarification gerekiyorsa doğrudan dön
        if decision.source == "clarify":
            reply = decision.clarify_text or "Bunu tam anlayamadım. Bir kez daha söyler misin?"
            self.dialogue.update(cleaned, reply, intent)
            return BrainResult(reply_text=reply, intent=intent)

        # 4) deterministic skill
        if decision.source == "skill":
            skill_result = self.skills.handle(intent, cleaned)
            if skill_result:
                self.dialogue.update(cleaned, skill_result, intent)
                return BrainResult(reply_text=skill_result, intent=intent)

        # 5) template sistemi (şimdilik basit fallback)
        if decision.source == "template":
            template_reply = self._handle_template_reply(intent, cleaned)
            self.dialogue.update(cleaned, template_reply, intent)
            return BrainResult(reply_text=template_reply, intent=intent)

        # 6) LLM fallback
        prompt = self._build_prompt(cleaned)

        raw = self.llm.generate(prompt)
        answer = self.policy.apply(raw)

        self.dialogue.update(cleaned, answer, intent)
        return BrainResult(reply_text=answer, intent=intent)

    def _build_prompt(self, cleaned: str) -> str:
        context = self.dialogue.get_context()

        context_block = ""
        if context.get("last_user") and context.get("last_bot"):
            context_block = f"""
Önceki kısa bağlam:
Kullanıcı: {context["last_user"]}
Poodle: {context["last_bot"]}
""".strip()

        prompt = f"""
{self.system_prompt}

{context_block}

Kullanıcı:
{cleaned}
""".strip()

        return prompt

    def _handle_template_reply(self, intent: str, text: str) -> str:
        t = (text or "").strip().lower()

        if intent == "smalltalk_short":
            return "Anladım."

        if intent == "followup":
            return "Bunu biraz daha açar mısın?"

        if t in {"tamam", "peki", "olur"}:
            return "Tamam."

        return "Anladım."
