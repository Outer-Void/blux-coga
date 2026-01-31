# Repository Snapshot

## 1) Metadata
- Repository name: blux-coga
- Organization / owner: unknown
- Default branch (if detectable): work
- HEAD commit hash (if available): deef29e5bfccab4fc9374d31d8d3482d8cb7ba76
- Snapshot timestamp (UTC): 2026-01-31T06:04:38Z
- Total file count (excluding directories): 24
- Description: Python package named blux-coga with dialogue/core modules and tests.

## 2) Repository Tree
.
  README.md [text]
  pyproject.toml [text]
  src/
    blux_coga/
      __init__.py [text]
      __main__.py [text]
      core/
        __init__.py [text]
        boundaries.py [text]
        constants.py [text]
        state.py [text]
        thinker.py [text]
      dialogue/
        __init__.py [text]
        engine.py [text]
        reflection.py [text]
      io/
        __init__.py [text]
        cli.py [text]
    blux_coga.egg-info/
      PKG-INFO [text]
      SOURCES.txt [text]
      dependency_links.txt [text]
      entry_points.txt [text]
      top_level.txt [text]
  tests/
    test_conversation_continuity.py [text]
    test_no_execution_language.py [text]
    test_non_directive_behavior.py [text]
    test_phase2_features.py [text]
    test_stop_condition.py [text]

## 3) FULL FILE CONTENTS (MANDATORY)

FILE: README.md
Kind: text
Size: 11
Last modified: 2026-01-31T06:02:58Z

CONTENT:
# blux-coga

FILE: pyproject.toml
Kind: text
Size: 295
Last modified: 2026-01-31T06:02:58Z

CONTENT:
[project]
name = "blux-coga"
version = "0.1.0"
description = "BLUX-CogA conversational reasoning scaffold"
readme = "README.md"
requires-python = ">=3.10"

[project.scripts]
blux-coga = "blux_coga.io.cli:main"

[tool.pytest.ini_options]
addopts = "-q"
testpaths = ["tests"]
pythonpath = ["src"]


FILE: src/blux_coga.egg-info/PKG-INFO
Kind: text
Size: 183
Last modified: 2026-01-31T06:02:58Z

CONTENT:
Metadata-Version: 2.4
Name: blux-coga
Version: 0.1.0
Summary: BLUX-CogA conversational reasoning scaffold
Requires-Python: >=3.10
Description-Content-Type: text/markdown

# blux-coga


FILE: src/blux_coga.egg-info/SOURCES.txt
Kind: text
Size: 684
Last modified: 2026-01-31T06:02:58Z

CONTENT:
README.md
pyproject.toml
src/blux_coga/__init__.py
src/blux_coga/__main__.py
src/blux_coga.egg-info/PKG-INFO
src/blux_coga.egg-info/SOURCES.txt
src/blux_coga.egg-info/dependency_links.txt
src/blux_coga.egg-info/entry_points.txt
src/blux_coga.egg-info/top_level.txt
src/blux_coga/core/__init__.py
src/blux_coga/core/boundaries.py
src/blux_coga/core/state.py
src/blux_coga/core/thinker.py
src/blux_coga/dialogue/__init__.py
src/blux_coga/dialogue/engine.py
src/blux_coga/dialogue/reflection.py
src/blux_coga/io/__init__.py
src/blux_coga/io/cli.py
tests/test_conversation_continuity.py
tests/test_no_execution_language.py
tests/test_non_directive_behavior.py
tests/test_stop_condition.py

FILE: src/blux_coga.egg-info/dependency_links.txt
Kind: text
Size: 1
Last modified: 2026-01-31T06:02:58Z

CONTENT:



FILE: src/blux_coga.egg-info/entry_points.txt
Kind: text
Size: 52
Last modified: 2026-01-31T06:02:58Z

CONTENT:
[console_scripts]
blux-coga = blux_coga.io.cli:main


FILE: src/blux_coga.egg-info/top_level.txt
Kind: text
Size: 10
Last modified: 2026-01-31T06:02:58Z

CONTENT:
blux_coga


FILE: src/blux_coga/__init__.py
Kind: text
Size: 74
Last modified: 2026-01-31T06:02:58Z

CONTENT:
"""BLUX-CogA package."""

__all__ = ["__version__"]
__version__ = "0.1.0"


FILE: src/blux_coga/__main__.py
Kind: text
Size: 114
Last modified: 2026-01-31T06:02:58Z

CONTENT:
"""Module entrypoint for blux_coga."""

from blux_coga.io.cli import main


if __name__ == "__main__":
    main()


FILE: src/blux_coga/core/__init__.py
Kind: text
Size: 0
Last modified: 2026-01-31T06:02:58Z

CONTENT:


FILE: src/blux_coga/core/boundaries.py
Kind: text
Size: 1036
Last modified: 2026-01-31T06:02:58Z

CONTENT:
"""Boundary enforcement for non-directive language."""

from __future__ import annotations

import re
from typing import Iterable


_BANNED_PHRASES = (
    "you should",
    "i recommend",
    "best approach",
    "next step",
    "do this",
    "you need to",
    "i suggest you",
)

_IMPERATIVE_STARTS = (
    "do ",
    "try ",
    "make ",
    "create ",
    "build ",
    "run ",
    "use ",
    "consider ",
    "choose ",
    "pick ",
    "decide ",
)


def _sentences(text: str) -> Iterable[str]:
    for sentence in re.split(r"[.!?]+", text):
        cleaned = sentence.strip().lower()
        if cleaned:
            yield cleaned


def has_violation(text: str) -> bool:
    lowered = text.lower()
    if any(phrase in lowered for phrase in _BANNED_PHRASES):
        return True
    for sentence in _sentences(text):
        if sentence.startswith(_IMPERATIVE_STARTS):
            return True
    return False


def enforce(text: str, fallback: str) -> str:
    if has_violation(text):
        return fallback
    return text


FILE: src/blux_coga/core/constants.py
Kind: text
Size: 61
Last modified: 2026-01-31T06:02:58Z

CONTENT:
"""Shared constants for CogA."""

MODEL_VERSION = "CogA-0.1"


FILE: src/blux_coga/core/state.py
Kind: text
Size: 925
Last modified: 2026-01-31T06:02:58Z

CONTENT:
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


FILE: src/blux_coga/core/thinker.py
Kind: text
Size: 881
Last modified: 2026-01-31T06:02:58Z

CONTENT:
"""CogA thinker wrapper."""

from __future__ import annotations

from blux_coga.core.constants import MODEL_VERSION
from blux_coga.core.state import SessionState
from blux_coga.dialogue.engine import Response, generate_response


class CogAThinker:
    def __init__(self) -> None:
        self.state = SessionState()

    def respond(self, user_input: str) -> Response:
        if self.state.frozen:
            return Response(text="", metadata={"model_version": MODEL_VERSION})
        self.state.add_turn("user", user_input)
        self.state.add_user_utterance(user_input)
        response = generate_response(user_input, self.state)
        self.state.add_turn("assistant", response.text)
        if not self.state.stopped and not self.state.frozen:
            self.state.last_intent = user_input
            self.state.extracted_intent = user_input
        return response


FILE: src/blux_coga/dialogue/__init__.py
Kind: text
Size: 0
Last modified: 2026-01-31T06:02:58Z

CONTENT:


FILE: src/blux_coga/dialogue/engine.py
Kind: text
Size: 5573
Last modified: 2026-01-31T06:02:58Z

CONTENT:
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


FILE: src/blux_coga/dialogue/reflection.py
Kind: text
Size: 392
Last modified: 2026-01-31T06:02:58Z

CONTENT:
"""Reflection and clarification helpers."""

from __future__ import annotations


def build_reflection(intent: str) -> str:
    cleaned = intent.strip()
    return f"What I'm hearing is: {cleaned}."


def build_clarification(intent: str) -> str:
    return (
        "What feels unclear or unsettled about that for you?"
        if intent
        else "What would you like to explore?"
    )


FILE: src/blux_coga/io/__init__.py
Kind: text
Size: 0
Last modified: 2026-01-31T06:02:58Z

CONTENT:


FILE: src/blux_coga/io/cli.py
Kind: text
Size: 463
Last modified: 2026-01-31T06:02:58Z

CONTENT:
"""CLI harness for CogA."""

from __future__ import annotations

from blux_coga.core.thinker import CogAThinker


def main() -> None:
    thinker = CogAThinker()
    while True:
        try:
            user_input = input("> ")
        except EOFError:
            break
        response = thinker.respond(user_input)
        print(response.text)
        if thinker.state.stopped or thinker.state.frozen:
            break


if __name__ == "__main__":
    main()


FILE: tests/test_conversation_continuity.py
Kind: text
Size: 308
Last modified: 2026-01-31T06:02:58Z

CONTENT:
from blux_coga.core.thinker import CogAThinker


def test_conversation_continuity():
    thinker = CogAThinker()
    first = "I want to talk about how tired I feel lately."
    thinker.respond(first)
    response = thinker.respond("That has been hard.")
    assert "how tired I feel lately" in response.text


FILE: tests/test_no_execution_language.py
Kind: text
Size: 332
Last modified: 2026-01-31T06:02:58Z

CONTENT:
from blux_coga.core.thinker import CogAThinker


def test_no_execution_language():
    thinker = CogAThinker()
    response = thinker.respond("I feel stuck about my options.")
    lowered = response.text.lower()
    for phrase in ("you should", "the best approach", "i recommend", "next step"):
        assert phrase not in lowered


FILE: tests/test_non_directive_behavior.py
Kind: text
Size: 330
Last modified: 2026-01-31T06:02:58Z

CONTENT:
from blux_coga.core.thinker import CogAThinker


def test_non_directive_behavior():
    thinker = CogAThinker()
    response = thinker.respond("I'm deciding whether to change jobs.")
    lowered = response.text.lower()
    for phrase in ("recommend", "should", "best", "next step", "decide"):
        assert phrase not in lowered


FILE: tests/test_phase2_features.py
Kind: text
Size: 1243
Last modified: 2026-01-31T06:02:58Z

CONTENT:
from blux_coga.core.thinker import CogAThinker


def test_ambiguity_labeling():
    thinker = CogAThinker()
    response = thinker.respond("idk")
    assert "ambiguous/underspecified" in response.text
    assert "?" in response.text


def test_contradiction_detection():
    thinker = CogAThinker()
    thinker.respond("I want apples")
    response = thinker.respond("I don't want apples")
    lowered = response.text.lower()
    assert "potential contradiction noticed" in lowered
    assert "which one reflects what you mean right now?" in lowered


def test_summarize_command():
    thinker = CogAThinker()
    thinker.respond("I'm thinking about changing my routine.")
    thinker.respond("It feels hard to keep going.")
    response = thinker.respond("summarize")
    lowered = response.text.lower()
    assert "what i'm hearing is" in lowered
    for phrase in ("you should", "i recommend", "best approach", "next step"):
        assert phrase not in lowered


def test_freeze_command_exits():
    thinker = CogAThinker()
    response = thinker.respond("freeze")
    assert thinker.state.frozen is True
    assert "intent frozen" in response.text.lower()
    follow_up = thinker.respond("Anything else?")
    assert follow_up.text == ""


FILE: tests/test_stop_condition.py
Kind: text
Size: 220
Last modified: 2026-01-31T06:02:58Z

CONTENT:
from blux_coga.core.thinker import CogAThinker


def test_stop_condition():
    thinker = CogAThinker()
    response = thinker.respond("stop")
    assert thinker.state.stopped is True
    assert "?" not in response.text


## 4) Workflow Inventory (index only)
none

## 5) Search Index (raw results)

subprocess:
none

os.system:
none

exec(:
none

spawn:
none

shell:
none

child_process:
none

policy:
none

ethic:
none

enforce:
src/blux_coga/core/boundaries.py
src/blux_coga/dialogue/engine.py

guard:
none

receipt:
none

token:
src/blux_coga/dialogue/engine.py

signature:
none

verify:
none

capability:
none

key_id:
none

contract:
none

schema:
none

$schema:
none

json-schema:
none

router:
none

orchestr:
none

execute:
none

command:
tests/test_phase2_features.py

## 6) Notes
none