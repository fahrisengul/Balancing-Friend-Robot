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
        decision = self.policy.choose_source(cleaned, intent)

        # 🔴 CLARIFY
        if decision.source == "clarify":
            reply = decision.clarify_text
            self.dialogue.update(cleaned, reply, intent)
            return BrainResult(reply_text=reply, intent=intent)

        # 🔹 TEMPLATE / DETERMINISTIC
        if decision.source == "template":
            reply = self._handle_template(intent, cleaned)
            self.dialogue.update(cleaned, reply, intent)
            return BrainResult(reply_text=reply, intent=intent)

        # 🔹 LLM
        prompt = self._build_prompt(cleaned)

        raw = self.llm.generate(prompt)
        answer = self.policy.apply(raw)

        self.dialogue.update(cleaned, answer, intent)

        return BrainResult(reply_text=answer, intent=intent)

    # ---------------------------------------------------------

    def _handle_template(self, intent: str, text: str) -> str:
        t = text.lower()

        if intent == "greeting":
            return "Selam, buradayım."

        if intent == "farewell":
            return "Görüşürüz."

        if intent == "ask_name":
            return "Benim adım Poodle."

        if intent == "ask_identity":
            return "Ben seninle konuşan robot arkadaşınım."

        if intent == "ask_status":
            return "İyiyim, teşekkür ederim. Sen nasılsın?"

        if intent == "followup_repair":
            return "Tam olarak neyi sormak istemiştin?"

        if intent == "statement":
            return "Anladım."

        return "Tam anlayamadım. Biraz daha açar mısın?"

    # ---------------------------------------------------------

    def _build_prompt(self, cleaned: str) -> str:
        context = self.dialogue.get_context()

        context_block = ""
        if context.get("last_user") and context.get("last_bot"):
            context_block = f"""
Önceki konuşma:
Kullanıcı: {context["last_user"]}
Poodle: {context["last_bot"]}
""".strip()

        return f"""
{self.system_prompt}

{context_block}

Kullanıcı:
{cleaned}

Kısa ve doğal cevap ver.
""".strip()
