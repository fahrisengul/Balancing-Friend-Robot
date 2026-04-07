import threading
import time
from typing import Optional

from .behavior_state_machine import BehaviorStateMachine


class RobotOrchestrator:
    """
    Speech + Brain + Character UI + State Machine
    """

    def __init__(self, face, speech, brain):
        self.face = face
        self.speech = speech
        self.brain = brain

        self.state_machine = BehaviorStateMachine()

        self.is_busy = False
        self.last_interaction_time = time.time()

    # ---------------------------------------------------------
    # PUBLIC
    # ---------------------------------------------------------
    def start(self):
        self.speech.start_auto_listener()
        self._set_character_state("idle")

    def stop(self):
        self.speech.stop_auto_listener()

    def handle_pending_speech_events(self):
        if self.is_busy:
            return

        evt = self.speech.get_pending_event()
        evt_type = evt.get("type", "none")

        if evt_type == "none":
            return

        if evt_type == "sleep":
            self._on_sleep()
            return

        if evt_type == "resumed":
            self._on_resumed()
            return

        if evt_type == "clarify":
            self._on_clarify(evt.get("text"))
            return

        if evt_type == "command":
            text = evt.get("text")
            if text:
                threading.Thread(
                    target=self._process_user_command,
                    args=(text,),
                    daemon=True
                ).start()
            return

    # ---------------------------------------------------------
    # EVENT HANDLERS
    # ---------------------------------------------------------
    def _on_sleep(self):
        self.state_machine.transition("mute")
        self._sync_face()
        self.last_interaction_time = time.time()

    def _on_resumed(self):
        self.state_machine.transition("wake")
        self._sync_face()
        self.last_interaction_time = time.time()

    def _on_clarify(self, clarify_text: Optional[str]):
        if not clarify_text:
            clarify_text = "Seni tam anlayamadım. Bir daha söyler misin?"

        threading.Thread(
            target=self._speak_direct,
            args=(clarify_text,),
            daemon=True
        ).start()

    def _process_user_command(self, user_text: str):
        cleaned = (user_text or "").strip()
        if not cleaned:
            return

        bad_inputs = {"hey", "tamam", "peki", "evet", "hmm"}
        if cleaned.lower() in bad_inputs:
            return

        self._set_busy(True)

        try:
            self.state_machine.transition("speech_started")
            self._sync_face()

            self.state_machine.transition("stt_good")
            self._sync_face()

            result = self.brain.handle_user_input(cleaned)

            self.state_machine.transition("reply_ready")
            self._sync_face()

            reply_text = result.reply_text if hasattr(result, "reply_text") else str(result)
            self.speech.speak(reply_text)

            self.state_machine.transition("done")
            self._sync_face()

        except Exception as e:
            print(f">>> [ORCHESTRATOR ERROR] {type(e).__name__}: {e}")
            try:
                self.state_machine.transition("error")
                self._sync_face()
                self.speech.speak("Şu an küçük bir sorun yaşadım. Bir daha söyler misin?")
                self.state_machine.transition("recover")
                self._sync_face()
            except Exception:
                pass

        finally:
            self.last_interaction_time = time.time()
            self._set_busy(False)

    def _speak_direct(self, text: str):
        if not text:
            return

        self._set_busy(True)

        try:
            self.state_machine.set_state("speaking")
            self._sync_face()

            self.speech.speak(text)

            self.state_machine.transition("done")
            self._sync_face()

        except Exception as e:
            print(f">>> [SPEAK DIRECT ERROR] {type(e).__name__}: {e}")
            try:
                self.state_machine.set_state("error")
                self._sync_face()
            except Exception:
                pass

        finally:
            self.last_interaction_time = time.time()
            self._set_busy(False)

    # ---------------------------------------------------------
    # HELPERS
    # ---------------------------------------------------------
    def _set_busy(self, value: bool):
        self.is_busy = value
        self.speech.set_busy(value)

    def _sync_face(self):
        self._set_character_state(self.state_machine.state)

    def _set_character_state(self, state: str):
        try:
            self.face.set_state(state)
        except Exception:
            pass
