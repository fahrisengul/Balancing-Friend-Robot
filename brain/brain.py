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

        context = self.dialogue.get_context()

        # 1) intent tespit et (context ile)
        intent = self.intent.detect(cleaned, context=context)

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
            template_reply = self.memory.get_template(intent) or self._handle_template_reply(intent, cleaned, context)

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
            skill_result = self.skills.handle(intent, cleaned, context=context)
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
        prompt = self._build_prompt(cleaned, context=context, memories=memories)

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

    def _build_prompt(self, cleaned: str, context=None, memories=None) -> str:
        context = context or {}
        history_text = self.dialogue.get_recent_turns_as_text(limit=3)

        context_block = ""
        if history_text:
            context_block = f"""
Önceki kısa konuşma:
{history_text}
""".strip()

        topic_block = ""
        current_topic = context.get("current_topic")
        if current_topic:
            topic_block = f"Mevcut konu: {current_topic}"

        memory_block = ""
        if memories:
            lines = "\n".join(f"- {m}" for m in memories)
            memory_block = f"""
İlgili hafıza:
{lines}
""".strip()

        prompt = f"""
{self.system_prompt}

{topic_block}

{context_block}

{memory_block}

Kullanıcı:
{cleaned}

Kurallar:
- Kısa ve doğal cevap ver.
- Gerekirse önceki konuşmayı dikkate al.
- Kullanıcının son cümlesine doğrudan cevap ver.
- Saçma tekrar yapma.
""".strip()

        return prompt

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
            pass
