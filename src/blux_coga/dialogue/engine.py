"""Conversation engine for CogA."""

from __future__ import annotations

from dataclasses import dataclass

import re

from blux_coga.core.boundaries import enforce
from blux_coga.core.constants import MODEL_VERSION
from blux_coga.core.state import SessionState
from blux_coga.dialogue.reflection import build_clarification, build_reflection


@dataclass(frozen=True)
class Response:
    text: str
    metadata: dict


def _is_stop(text: str) -> bool:
    lowered = text.strip().lower()
    return lowered in {"stop", "that's enough", "that is enough"}


def _is_freeze(text: str) -> bool:
    return text.strip().lower() == "freeze"


def _is_summarize(text: str) -> bool:
    return text.strip().lower() == "summarize"


def _is_short_or_vague(text: str) -> bool:
    lowered = text.strip().lower()
    if len(lowered) < 6:
        return True
    if lowered in {"idk", "whatever", "nothing"}:
        return True
    return False


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
    return False


def _resolve_intent(text: str, state: SessionState) -> str:
    lowered = text.lower()
    if any(token in lowered for token in ("that", "it", "this")) and state.last_intent:
        return state.last_intent
    return text


def _normalize(text: str) -> str:
    cleaned = re.sub(r"[^\w\s]", "", text.lower())
    return re.sub(r"\s+", " ", cleaned).strip()


def _parse_position(text: str) -> tuple[bool, str] | None:
    normalized = _normalize(text)
    patterns = (
        ("i dont want", False),
        ("i want", True),
        ("i dont care", False),
        ("i care", True),
    )
    for prefix, polarity in patterns:
        if normalized.startswith(prefix):
            remainder = normalized[len(prefix) :].strip()
            if not remainder:
                return None
            topic = remainder.split()[0]
            return polarity, topic
    return None


def _detect_contradiction(
    current_text: str, previous_texts: list[str]
) -> tuple[str, str] | None:
    current_statement = _parse_position(current_text)
    if not current_statement:
        return None
    current_polarity, current_topic = current_statement
    for previous in reversed(previous_texts):
        previous_statement = _parse_position(previous)
        if not previous_statement:
            continue
        prev_polarity, prev_topic = previous_statement
        if prev_topic == current_topic and prev_polarity != current_polarity:
            return previous, current_text
    return None


def _summarize_intent(state: SessionState) -> str:
    intent = state.extracted_intent
    if not intent:
        for utterance in reversed(state.last_user_utterances):
            lowered = utterance.strip().lower()
            if lowered and lowered not in {"summarize", "freeze"}:
                intent = utterance
                break
    if not intent:
        intent = "no clear intent yet"
    open_questions = state.extracted_constraints[:2]
    questions_text = ", ".join(open_questions) if open_questions else "None yet."
    return f"What I'm hearing is: {intent}.\nOpen questions: {questions_text}"


def generate_response(user_input: str, state: SessionState) -> Response:
    if state.frozen:
        return Response(text="", metadata={"model_version": MODEL_VERSION})

    if _is_freeze(user_input):
        state.frozen = True
        state.stopped = True
        acknowledgment = "Intent frozen. I'll stop here."
        return Response(text=acknowledgment, metadata={"model_version": MODEL_VERSION})

    if _is_stop(user_input):
        state.stopped = True
        acknowledgment = "Acknowledged. I'll stop here."
        return Response(text=acknowledgment, metadata={"model_version": MODEL_VERSION})

    if _is_summarize(user_input):
        summary = _summarize_intent(state)
        intent = state.extracted_intent or ""
        fallback = "\n".join([build_reflection(intent), build_clarification(intent)])
        safe_text = enforce(summary, fallback)
        return Response(text=safe_text, metadata={"model_version": MODEL_VERSION})

    contradiction = _detect_contradiction(
        user_input, state.last_user_utterances[:-1]
    )
    if contradiction:
        earlier, later = contradiction
        text = (
            "Potential contradiction noticed: "
            f"earlier you said \"{earlier}\", later you said \"{later}\".\n"
            "Which one reflects what you mean right now?"
        )
        fallback = "\n".join(
            [build_reflection(user_input), build_clarification(user_input)]
        )
        safe_text = enforce(text, fallback)
        return Response(text=safe_text, metadata={"model_version": MODEL_VERSION})

    intent = _resolve_intent(user_input, state)
    reflection = build_reflection(intent)
    pieces = [reflection]

    if _is_short_or_vague(user_input):
        pieces.append("This feels ambiguous/underspecified.")
        pieces.append(build_clarification(intent))
    elif _detect_ambiguity(user_input):
        pieces.append(build_clarification(intent))

    text = "\n".join(pieces)
    fallback = "\n".join([reflection, build_clarification(intent)])
    safe_text = enforce(text, fallback)
    return Response(text=safe_text, metadata={"model_version": MODEL_VERSION})
