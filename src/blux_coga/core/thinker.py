"""CogA thinker wrapper."""

from __future__ import annotations

from blux_coga.core.state import SessionState
from blux_coga.dialogue.engine import Response, generate_response


class CogAThinker:
    def __init__(self) -> None:
        self.state = SessionState()

    def respond(self, user_input: str) -> Response:
        self.state.add_turn("user", user_input)
        response = generate_response(user_input, self.state)
        self.state.add_turn("assistant", response.text)
        if not self.state.stopped:
            self.state.last_intent = user_input
        return response
