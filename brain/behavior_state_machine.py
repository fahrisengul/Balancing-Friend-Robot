class BehaviorStateMachine:
    VALID_STATES = {
        "idle",
        "attentive",
        "listening",
        "thinking",
        "speaking",
        "muted",
        "error",
    }

    def __init__(self):
        self.state = "idle"

    def set_state(self, state: str) -> str:
        if state not in self.VALID_STATES:
            raise ValueError(f"Geçersiz state: {state}")
        self.state = state
        return self.state

    def transition(self, event: str) -> str:
        if self.state == "idle":
            if event == "audio_detected":
                self.state = "attentive"
            elif event == "mute":
                self.state = "muted"

        elif self.state == "attentive":
            if event == "speech_started":
                self.state = "listening"
            elif event == "reply_ready":
                self.state = "speaking"
            elif event == "mute":
                self.state = "muted"
            elif event == "timeout":
                self.state = "idle"

        elif self.state == "listening":
            if event == "stt_good":
                self.state = "thinking"
            elif event == "stt_bad":
                self.state = "attentive"
            elif event == "mute":
                self.state = "muted"
            elif event == "error":
                self.state = "error"

        elif self.state == "thinking":
            if event == "reply_ready":
                self.state = "speaking"
            elif event == "error":
                self.state = "error"

        elif self.state == "speaking":
            if event == "done":
                self.state = "idle"
            elif event == "mute":
                self.state = "muted"
            elif event == "error":
                self.state = "error"

        elif self.state == "muted":
            if event == "wake":
                self.state = "attentive"
            elif event == "error":
                self.state = "error"

        elif self.state == "error":
            if event == "recover":
                self.state = "idle"

        return self.state
