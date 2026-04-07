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

        # clarify
        if decision.source == "clarify":
            reply = decision.clarify_text or "Seni tam anlayamadım. Tekrar söyler misin?"
            self.dialogue.update(cleaned, reply, intent)
            return BrainResult(reply_text=reply, intent=intent)

        # deterministic skill
        if decision.source == "skill":
            skill_result = self.skills.handle(intent, cleaned)
            if skill_result:
                self.dialogue.update(cleaned, skill_result, intent)
                return BrainResult(reply_text=skill_result, intent=intent)

        # template
        if decision.source == "template":
            reply = self._handle_template(intent, cleaned)
            self.dialogue.update(cleaned, reply, intent)
            return BrainResult(reply_text=reply, intent=intent)

        # llm
        prompt = self._build_prompt(cleaned)
        raw = self.llm.generate(prompt)
        answer = self.policy.apply(raw)

        self.dialogue.update(cleaned, answer, intent)
        return BrainResult(reply_text=answer, intent=intent)

    def _handle_template(self, intent: str, text: str) -> str:
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

        if intent == "thanks":
            return "Rica ederim."

        if intent == "acknowledge":
            return "Tamam."

        if intent == "followup_repair":
            return "Tam olarak neyi sormak istemiştin?"

        if intent == "statement":
            return "Anladım."

        return "Biraz daha açık söyler misin?"

    def _build_prompt(self, cleaned: str) -> str:
        context = self.dialogue.get_context()
        history_block = self.dialogue.get_recent_turns_as_text(limit=3)

        topic = context.get("current_topic")
        topic_line = f"Mevcut konu: {topic}" if topic else ""

        return f"""
{self.system_prompt}

{topic_line}

Önceki kısa konuşma:
{history_block}

Kullanıcı:
{cleaned}

Kurallar:
- Her zaman Türkçe cevap ver.
- 1-2 kısa cümle kullan.
- Soruya direkt cevap ver.
- Gereksiz neşe sesleri veya İngilizce kullanma.
""".strip()
