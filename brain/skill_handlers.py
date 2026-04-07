from datetime import date, datetime
from typing import Optional


class SkillHandlers:
    """
    Deterministic cevaplar.
    Buradaki temel kural:
    - güvenli
    - test edilebilir
    - kısa
    - LLM'siz
    """

    def __init__(self):
        # Şimdilik fallback profile bilgileri
        # Sonraki adımda bunları memory_manager / SQLite'dan okuyacağız.
        self.robot_name = "Poodle"
        self.user_name = "Tanem"
        self.birth_date = date(2013, 5, 30)

    def handle(self, intent: str, text: str = "", context: Optional[dict] = None) -> Optional[str]:
        t = (text or "").strip().lower()

        if intent == "greeting":
            return self._handle_greeting()

        if intent == "ask_name":
            return self._handle_ask_name()

        if intent == "ask_identity":
            return self._handle_ask_identity()

        if intent == "ask_status":
            return self._handle_ask_status()

        if intent == "thanks":
            return self._handle_thanks()

        if intent == "acknowledge":
            return self._handle_acknowledge()

        if intent == "ask_birthdate":
            return self._handle_birthdate()

        if intent == "ask_age":
            return self._handle_age(t)

        if intent == "ask_day_date":
            return self._handle_day_date()

        if intent == "ask_time":
            return self._handle_time()

        if intent == "mute":
            return "Tamam, sessiz moda geçiyorum."

        if intent == "wake":
            return "Buradayım."

        if intent == "ask_activity":
            return self._handle_activity()

        return None

    # ---------------------------------------------------------
    # Greeting / identity
    # ---------------------------------------------------------
    def _handle_greeting(self) -> str:
        return f"Selam, ben {self.robot_name}."

    def _handle_ask_name(self) -> str:
        return f"Benim adım {self.robot_name}."

    def _handle_ask_identity(self) -> str:
        return f"Ben {self.robot_name}. Seninle konuşan robot arkadaşınım."

    def _handle_ask_status(self) -> str:
        return "İyiyim, teşekkür ederim. Sen nasılsın?"

    def _handle_thanks(self) -> str:
        return "Rica ederim."

    def _handle_acknowledge(self) -> str:
        return "Tamam."

    # ---------------------------------------------------------
    # Time / date / age
    # ---------------------------------------------------------
    def _handle_birthdate(self) -> str:
        return f"Doğum günün {self.birth_date.day} Mayıs."

    def _handle_age(self, text: str) -> str:
        today = date.today()
        current_age = today.year - self.birth_date.year - (
            (today.month, today.day) < (self.birth_date.month, self.birth_date.day)
        )
        next_age = current_age + 1

        if "girecegim" in text or "gireceğim" in text:
            return f"Bir sonraki doğum gününde {next_age} yaşına gireceksin."

        return f"Şu anda {current_age} yaşındasın."

    def _handle_day_date(self) -> str:
        today = datetime.now()
        weekdays = {
            0: "Pazartesi",
            1: "Salı",
            2: "Çarşamba",
            3: "Perşembe",
            4: "Cuma",
            5: "Cumartesi",
            6: "Pazar",
        }
        months = {
            1: "Ocak",
            2: "Şubat",
            3: "Mart",
            4: "Nisan",
            5: "Mayıs",
            6: "Haziran",
            7: "Temmuz",
            8: "Ağustos",
            9: "Eylül",
            10: "Ekim",
            11: "Kasım",
            12: "Aralık",
        }
        return f"Bugün {today.day} {months[today.month]} {today.year}, günlerden {weekdays[today.weekday()]}."

    def _handle_time(self) -> str:
        now = datetime.now()
        return f"Saat şu an {now.strftime('%H:%M')}."

    # ---------------------------------------------------------
    # Short safe social replies
    # ---------------------------------------------------------
    def _handle_activity(self) -> str:
        return "Bugün seninle konuşmaya ve kendimi geliştirmeye odaklandım."
