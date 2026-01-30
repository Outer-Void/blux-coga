"""Boundary enforcement for non-directive language."""

from __future__ import annotations

import re
from typing import Iterable


_BANNED_PHRASES = (
    "you should",
    "the best approach",
    "i recommend",
    "next step",
    "do this",
    "you must",
    "you need to",
    "i suggest",
    "i advise",
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
