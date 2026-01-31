"""Contract models for CogA reasoning artifacts."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from blux_coga.core.state import SessionState, Turn


class VerdictStatus(str, Enum):
    COMPLETE = "COMPLETE"
    UNCLEAR = "UNCLEAR"
    REFUSE = "REFUSE"


@dataclass(frozen=True)
class ProblemSpec:
    user_input: str
    history: List[Turn] = field(default_factory=list)
    last_user_utterances: List[str] = field(default_factory=list)
    last_intent: Optional[str] = None
    extracted_intent: Optional[str] = None
    extracted_constraints: List[str] = field(default_factory=list)
    stopped: bool = False
    frozen: bool = False

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "ProblemSpec":
        session = payload.get("session", {})
        history_payload = session.get("history", [])
        history = [Turn(**turn) for turn in history_payload]
        return cls(
            user_input=payload.get("user_input", ""),
            history=history,
            last_user_utterances=list(session.get("last_user_utterances", [])),
            last_intent=session.get("last_intent"),
            extracted_intent=session.get("extracted_intent"),
            extracted_constraints=list(session.get("extracted_constraints", [])),
            stopped=bool(session.get("stopped", False)),
            frozen=bool(session.get("frozen", False)),
        )

    @classmethod
    def from_session_state(cls, user_input: str, state: SessionState) -> "ProblemSpec":
        return cls(
            user_input=user_input,
            history=list(state.history),
            last_user_utterances=list(state.last_user_utterances),
            last_intent=state.last_intent,
            extracted_intent=state.extracted_intent,
            extracted_constraints=list(state.extracted_constraints),
            stopped=state.stopped,
            frozen=state.frozen,
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_input": self.user_input,
            "session": {
                "history": [
                    {"speaker": turn.speaker, "text": turn.text}
                    for turn in self.history
                ],
                "last_user_utterances": list(self.last_user_utterances),
                "last_intent": self.last_intent,
                "extracted_intent": self.extracted_intent,
                "extracted_constraints": list(self.extracted_constraints),
                "stopped": self.stopped,
                "frozen": self.frozen,
            },
        }

    def to_session_state(self) -> SessionState:
        return SessionState(
            history=list(self.history),
            last_user_utterances=list(self.last_user_utterances),
            last_intent=self.last_intent,
            extracted_intent=self.extracted_intent,
            extracted_constraints=list(self.extracted_constraints),
            stopped=self.stopped,
            frozen=self.frozen,
        )


@dataclass(frozen=True)
class RunHeader:
    input_hash: str
    contract_version: str
    model_version: str

    def to_dict(self) -> Dict[str, str]:
        return {
            "input_hash": self.input_hash,
            "contract_version": self.contract_version,
            "model_version": self.model_version,
        }


@dataclass(frozen=True)
class Delta:
    minimal_change: str

    def to_dict(self) -> Dict[str, str]:
        return {"minimal_change": self.minimal_change}


@dataclass(frozen=True)
class Check:
    id: str
    status: str
    message: str

    def to_dict(self) -> Dict[str, str]:
        return {"id": self.id, "status": self.status, "message": self.message}


@dataclass(frozen=True)
class Option:
    id: str
    title: str
    pros: List[str] = field(default_factory=list)
    cons: List[str] = field(default_factory=list)
    risks: List[str] = field(default_factory=list)
    unknowns: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "pros": list(self.pros),
            "cons": list(self.cons),
            "risks": list(self.risks),
            "unknowns": list(self.unknowns),
        }


@dataclass(frozen=True)
class ComparisonRow:
    option_id: str
    values: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {"option_id": self.option_id, "values": list(self.values)}


@dataclass(frozen=True)
class ComparisonMatrix:
    criteria: List[str]
    rows: List[ComparisonRow]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "criteria": list(self.criteria),
            "rows": [row.to_dict() for row in self.rows],
        }


@dataclass(frozen=True)
class ThoughtArtifact:
    run_header: RunHeader
    reflection: str
    clarifications: List[str]
    observations: List[str]
    flags: Dict[str, bool]
    contradiction: Optional[Dict[str, str]]
    options: List[Option]
    comparison: Optional[ComparisonMatrix]
    acknowledgment: Optional[str]
    summary: Optional[str]
    response_text: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "run_header": self.run_header.to_dict(),
            "reflection": self.reflection,
            "clarifications": list(self.clarifications),
            "observations": list(self.observations),
            "flags": dict(self.flags),
            "contradiction": self.contradiction,
            "options": [option.to_dict() for option in self.options],
            "comparison": self.comparison.to_dict() if self.comparison else None,
            "acknowledgment": self.acknowledgment,
            "summary": self.summary,
            "response_text": self.response_text,
        }


@dataclass(frozen=True)
class ReasoningVerdict:
    run_header: RunHeader
    status: VerdictStatus
    checks: List[Check]
    delta: Optional[Delta]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "run_header": self.run_header.to_dict(),
            "status": self.status.value,
            "checks": [check.to_dict() for check in self.checks],
            "delta": self.delta.to_dict() if self.delta else None,
        }
