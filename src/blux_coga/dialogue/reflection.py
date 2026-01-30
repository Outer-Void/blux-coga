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
