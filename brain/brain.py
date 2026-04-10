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
        self.intent_router = IntentRouter()
        self.dialogue = DialogueManager()
        self.skills = SkillHandlers()
        self.policy = ResponsePolicy()
        self.llm = LLMClient()
        self.system_prompt = build_system_prompt()
        self.memory = MemoryManager()

    def handle_user_input(self, text: str) -> BrainResult:
        cleaned = (text or "").strip()

        if not cleaned:
            reply = "Seni tam anlayamadım. Tekrar söyler misin?"
            self.dialogue.update(cleaned, reply, "clarification_needed")
            return BrainResult(reply_text=reply, intent="clarification_needed")

        # 1) intent
        intent = self.intent_router.detect(cleaned)

        # 2) policy
        decision = self.policy.choose_source(cleaned, intent)

        # 3) clarify
        if decision.source == "clarify":
            reply = decision.clarify_text or "Bunu biraz daha açık söyler misin?"
            self.dialogue.update(cleaned, reply, intent)
            return BrainResult(reply_text=reply, intent=intent)

        # 4) deterministic skill
        if decision.source == "skill":
            skill_result = self.skills.handle(intent, cleaned)
            if skill_result:
                self.dialogue.update(cleaned, skill_result, intent)
                return BrainResult(reply_text=skill_result, intent=intent)

            # skill başarısızsa LLM fallback
            decision.source = "llm"

        # 5) template + optional followup
        if decision.source == "template":
            template = self.memory.get_template(intent_name=intent)

            if template:
                followup = self.memory.get_followup(intent_name=intent)
                reply = f"{template} {followup}".strip() if followup else template
                reply = self.policy.apply(reply)

                self.dialogue.update(cleaned, reply, intent)
                return BrainResult(reply_text=reply, intent=intent)

            # template yoksa LLM'e düş
            decision.source = "llm"

        # 6) LLM
        prompt = self._build_prompt(cleaned, intent)
        raw = self.llm.generate(prompt)
        answer = self.policy.apply(raw)

        self.dialogue.update(cleaned, answer, intent)
        return BrainResult(reply_text=answer, intent=intent)

    def _build_prompt(self, cleaned: str, intent: str) -> str:
        recent_turns = self.dialogue.get_recent_turns_as_text(limit=3)
        topic = self.dialogue.get_current_topic()

        person = self.memory.get_person_by_role("tanem")
        person_block = ""

        if person:
            facts = []

            name = person.get("name")
            grade = person.get("grade_level")
            school = person.get("school_name")
            notes = person.get("notes")

            if name:
                facts.append(f"Adı: {name}")
            if grade:
                facts.append(f"Sınıf: {grade}")
            if school:
                facts.append(f"Okul: {school}")
            if notes:
                facts.append(f"Not: {notes}")

            if facts:
                person_block = "Tanem hakkında ilgili bilgiler:\n- " + "\n- ".join(facts)

        topic_line = f"Konu: {topic}" if topic else "Konu: belirsiz"

        prompt = f"""
{self.system_prompt}

{person_block}

Son konuşma bağlamı:
{recent_turns}

Intent: {intent}
{topic_line}

Kullanıcı:
{cleaned}

Kurallar:
- Kullanıcının son cümlesine doğrudan cevap ver.
- İngilizce kullanma.
- 1-2 kısa cümle kullan.
- Gereksiz giriş cümlesi kurma.
- Tanem hakkında gereksiz profil bilgisi dökme.
- Kullanıcı soru sorduysa önce soruya cevap ver.
- Kullanıcı seni onu tanımaya davet ediyorsa, kısa ve doğal bir soru sor.
- Eğitim veya endişe sorularında somut ve kısa öneriler ver.
""".strip()

        return prompt
