class BehaviorStateMachine:

    def __init__(self):
        self.state = "idle"

    def transition(self, event: str):

        if self.state == "idle":
            if event == "audio":
                self.state = "listening"

        elif self.state == "listening":
            if event == "stt_done":
                self.state = "thinking"

        elif self.state == "thinking":
            if event == "reply_ready":
                self.state = "speaking"

        elif self.state == "speaking":
            if event == "done":
                self.state = "idle"

        return self.state
