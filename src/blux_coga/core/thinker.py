"""CogA thinker wrapper."""

from __future__ import annotations

from blux_coga.contracts.models import ProblemSpec, ReasoningVerdict, ThoughtArtifact
from blux_coga.contracts.processor import run_contract
from blux_coga.core.state import SessionState
from blux_coga.profiles import ProfileSpec


class CogAThinker:
    def __init__(
        self,
        state: SessionState | None = None,
        profile: ProfileSpec | None = None,
    ) -> None:
        self.state = state or SessionState()
        self.profile = profile

    def respond(self, user_input: str) -> tuple[ThoughtArtifact, ReasoningVerdict]:
        problem_spec = ProblemSpec.from_session_state(user_input, self.state)
        artifact, verdict, updated_state = run_contract(
            problem_spec,
            profile=self.profile,
        )
        self.state = updated_state
        return artifact, verdict
