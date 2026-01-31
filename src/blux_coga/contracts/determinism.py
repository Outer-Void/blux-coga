"""Deterministic normalization and hashing utilities."""

from __future__ import annotations

import hashlib
import json
from typing import Any, Dict

from blux_coga.contracts.models import ProblemSpec


def normalize_value(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: normalize_value(value[key]) for key in sorted(value.keys())}
    if isinstance(value, list):
        return [normalize_value(item) for item in value]
    return value


def normalize_problem_spec(problem_spec: ProblemSpec) -> Dict[str, Any]:
    return normalize_value(problem_spec.to_dict())


def stable_json_dumps(payload: Any) -> str:
    return json.dumps(
        payload,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
        allow_nan=False,
    )


def stable_hash_payload(payload: Any) -> str:
    encoded = stable_json_dumps(payload).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def stable_hash(problem_spec: ProblemSpec) -> str:
    normalized = normalize_problem_spec(problem_spec)
    return stable_hash_payload(normalized)
