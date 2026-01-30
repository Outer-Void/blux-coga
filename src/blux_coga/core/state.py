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
    last_user_utterances: List[str] = field(default_factory=list)
    last_intent: str | None = None
    extracted_intent: str | None = None
    extracted_constraints: List[str] = field(default_factory=list)
    stopped: bool = False
    frozen: bool = False

    def add_turn(self, speaker: str, text: str) -> None:
        self.history.append(Turn(speaker=speaker, text=text))

    def add_user_utterance(self, text: str, limit: int = 10) -> None:
        self.last_user_utterances.append(text)
        if len(self.last_user_utterances) > limit:
            self.last_user_utterances = self.last_user_utterances[-limit:]
