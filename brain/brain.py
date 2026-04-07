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
        normalized = cleaned.lower()

        # 1) intent tespit et
        intent = self.intent.detect(cleaned)

        # 2) response kaynağını seç
        decision = self.policy.choose_source(cleaned, intent)

        # 3) clarification
        if decision.source == "clarify":
            reply = (
                self.memory.get_template("clarify")
                or decision.clarify_text
                or "Bunu tam anlayamadım. Bir kez daha söyler misin?"
            )

            self.dialogue.update(cleaned, reply, intent)
            self._log_turn(
                raw_text=cleaned,
                normalized_text=normalized,
                intent=intent,
                response_source="clarify",
                reply_text=reply,
            )
            return BrainResult(reply_text=reply, intent=intent)

        # 4) template
        if decision.source == "template":
            template_reply = self.memory.get_template(intent) or self._handle_template_reply(intent, cleaned)

            self.dialogue.update(cleaned, template_reply, intent)
            self._log_turn(
                raw_text=cleaned,
                normalized_text=normalized,
                intent=intent,
                response_source="template",
                reply_text=template_reply,
            )
            return BrainResult(reply_text=template_reply, intent=intent)

        # 5) deterministic skill
        if decision.source == "skill":
            skill_result = self.skills.handle(intent, cleaned)
            if skill_result:
                self.dialogue.update(cleaned, skill_result, intent)
                self._log_turn(
                    raw_text=cleaned,
                    normalized_text=normalized,
                    intent=intent,
                    response_source="skill",
                    reply_text=skill_result,
                )
                return BrainResult(reply_text=skill_result, intent=intent)

            # skill bekleniyordu ama sonuç yoksa güvenli fallback
            fallback = "Bunu şu an net cevaplayamadım. Biraz daha açık sorar mısın?"
            self.dialogue.update(cleaned, fallback, intent)
            self._log_turn(
                raw_text=cleaned,
                normalized_text=normalized,
                intent=intent,
                response_source="skill_fallback",
                reply_text=fallback,
            )
            return BrainResult(reply_text=fallback, intent=intent)

        # 6) LLM fallback
        memories = self.memory.search_memories(cleaned, limit=3)
        prompt = self._build_prompt(cleaned, memories)

        raw = self.llm.generate(prompt)
        answer = self.policy.apply(raw)

        self.dialogue.update(cleaned, answer, intent)
        self._log_turn(
            raw_text=cleaned,
            normalized_text=normalized,
            intent=intent,
            response_source="llm",
            reply_text=answer,
        )

        return BrainResult(
            reply_text=answer,
            intent=intent,
            memory_used=memories if memories else None,
        )

    def _build_prompt(self, cleaned: str, memories=None) -> str:
        context = self.dialogue.get_context()

        context_block = ""
        if context.get("last_user") and context.get("last_bot"):
            context_block = f"""
Önceki kısa bağlam:
Kullanıcı: {context["last_user"]}
Poodle: {context["last_bot"]}
""".strip()

        memory_block = ""
        if memories:
            lines = "\n".join(f"- {m}" for m in memories)
            memory_block = f"""
İlgili hafıza:
{lines}
""".strip()

        prompt = f"""
{self.system_prompt}

{context_block}

{memory_block}

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

    def _log_turn(
        self,
        raw_text: str,
        normalized_text: str,
        intent: str,
        response_source: str,
        reply_text: str,
    ) -> None:
        try:
            self.memory.log_conversation(
                raw_text=raw_text,
                normalized_text=normalized_text,
                intent=intent,
                response_source=response_source,
                reply_text=reply_text,
            )
        except Exception:
            # Log başarısız olsa da konuşma akışı bozulmasın
            pass
