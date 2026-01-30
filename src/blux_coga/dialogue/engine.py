"""Conversation engine for CogA."""

from __future__ import annotations

from dataclasses import dataclass

from blux_coga.core.boundaries import enforce
from blux_coga.core.state import SessionState
from blux_coga.dialogue.reflection import build_clarification, build_reflection

MODEL_VERSION = "CogA-0.1-mini"


@dataclass(frozen=True)
class Response:
    text: str
    metadata: dict


def _is_stop(text: str) -> bool:
    lowered = text.strip().lower()
    return lowered in {"stop", "freeze", "that's enough", "that is enough"}


def _detect_ambiguity(text: str) -> bool:
    lowered = text.lower()
    ambiguous_markers = (
        "maybe",
        "not sure",
        "unsure",
        "kind of",
        "sort of",
        "somehow",
        "something",
    )
    if any(marker in lowered for marker in ambiguous_markers):
        return True
    if " or " in lowered:
        return True
    if len(text.split()) < 4:
        return True
    return False


def _resolve_intent(text: str, state: SessionState) -> str:
    lowered = text.lower()
    if any(token in lowered for token in ("that", "it", "this")) and state.last_intent:
        return state.last_intent
    return text


def generate_response(user_input: str, state: SessionState) -> Response:
    if _is_stop(user_input):
        state.stopped = True
        acknowledgment = "Acknowledged. I'll stop here."
        return Response(text=acknowledgment, metadata={"model_version": MODEL_VERSION})

    intent = _resolve_intent(user_input, state)
    reflection = build_reflection(intent)
    pieces = [reflection]

    if _detect_ambiguity(user_input):
        pieces.append(build_clarification(intent))

    text = "\n".join(pieces)
    safe_text = enforce(text, reflection)
    return Response(text=safe_text, metadata={"model_version": MODEL_VERSION})
