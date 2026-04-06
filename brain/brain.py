from .intent_router import IntentRouter
from .dialogue_manager import DialogueManager
from .skill_handlers import SkillHandlers
from .response_policy import ResponsePolicy
from .llm_client import LLMClient
from .persona import build_system_prompt
from .models import BrainResult


class PoodleBrain:

    def __init__(self):
        self.intent = IntentRouter()
        self.dialogue = DialogueManager()
        self.skills = SkillHandlers()
        self.policy = ResponsePolicy()
        self.llm = LLMClient()
        self.system_prompt = build_system_prompt()

    def handle_user_input(self, text: str) -> BrainResult:

        intent = self.intent.detect(text)

        # 1. Skill varsa direkt kullan
        skill_result = self.skills.handle(intent)
        if skill_result:
            self.dialogue.update(text, skill_result, intent)
            return BrainResult(reply_text=skill_result, intent=intent)

        # 2. LLM
        prompt = f"""
{self.system_prompt}

Kullanıcı:
{text}
"""

        raw = self.llm.generate(prompt)
        answer = self.policy.apply(raw)

        self.dialogue.update(text, answer, intent)

        return BrainResult(reply_text=answer, intent=intent)
