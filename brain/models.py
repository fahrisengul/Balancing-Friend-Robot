from dataclasses import dataclass
from typing import Optional, List


@dataclass
class BrainResult:
    reply_text: str
    intent: str
    state_hint: str = "speaking"
    memory_used: Optional[List[str]] = None
    action: Optional[str] = None
