from datetime import date


class SkillHandlers:
    def handle(self, intent: str):
        if intent == "ask_age":
            return self._age()

        if intent == "ask_birthdate":
            return "Doğum günün 30 Mayıs."

        if intent == "ask_activity":
            return "Bugün seninle konuşmaya ve sistemi daha iyi hale getirmeye odaklandım."

        return None

    def _age(self):
        today = date.today()
        birth_year = 2013
        age = today.year - birth_year
        return f"Şu anda {age} yaşındasın."
