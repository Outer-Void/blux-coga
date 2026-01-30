"""Session state for CogA conversations."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class Turn:
    speaker: str
    text: str


@dataclass
class SessionState:
    history: List[Turn] = field(default_factory=list)
    last_intent: str | None = None
    stopped: bool = False

    def add_turn(self, speaker: str, text: str) -> None:
        self.history.append(Turn(speaker=speaker, text=text))
