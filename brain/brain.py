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
        cleaned = (text or "").strip()
        intent = self.intent.detect(cleaned)

        # 1) Deterministic kısa ve güvenli cevaplar
        deterministic_reply = self._handle_deterministic_reply(cleaned, intent)
        if deterministic_reply:
            self.dialogue.update(cleaned, deterministic_reply, intent)
            return BrainResult(reply_text=deterministic_reply, intent=intent)

        # 2) Skill handler varsa onu kullan
        skill_result = self.skills.handle(intent)
        if skill_result:
            self.dialogue.update(cleaned, skill_result, intent)
            return BrainResult(reply_text=skill_result, intent=intent)

        # 3) LLM
        prompt = f"""
{self.system_prompt}

Kullanıcı:
{cleaned}
""".strip()

        raw = self.llm.generate(prompt)
        answer = self.policy.apply(raw)

        self.dialogue.update(cleaned, answer, intent)

        return BrainResult(reply_text=answer, intent=intent)

    def _handle_deterministic_reply(self, text: str, intent: str):
        t = text.lower().strip()

        # selamlaşma
        if intent == "greeting" or t in {"selam", "merhaba"}:
            return "Selam, ben Poodle."

        # isim sorusu
        if intent == "ask_name" or "adın ne" in t or "adin ne" in t:
            return "Benim adım Poodle."

        # kimlik sorusu
        if intent == "ask_identity" or "sen kimsin" in t:
            return "Ben Poodle. Seninle konuşan robot arkadaşınım."

        # durum sorusu
        if intent == "ask_status" or "nasılsın" in t or "nasilsin" in t:
            return "İyiyim, teşekkür ederim. Sen nasılsın?"

        # teşekkür
        if "teşekkür ederim" in t or "tesekkur ederim" in t:
            return "Rica ederim."

        # kısa onay
        if t in {"tamam", "peki"}:
            return "Tamam."

        return None
