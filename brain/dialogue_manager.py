class DialogueManager:

    def __init__(self):
        self.last_user = None
        self.last_bot = None
        self.last_intent = None

    def update(self, user, bot, intent):
        self.last_user = user
        self.last_bot = bot
        self.last_intent = intent

    def get_context(self):
        return {
            "last_user": self.last_user,
            "last_bot": self.last_bot,
            "last_intent": self.last_intent,
        }
