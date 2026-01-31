"""Profile loading utilities for deterministic CogA runs."""

from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import Any, Dict

from blux_coga.contracts.schema import validate_schema


PROFILE_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["profile_id", "profile_version", "device"],
    "properties": {
        "profile_id": {"type": "string"},
        "profile_version": {"type": "string"},
        "device": {"type": "string", "enum": ["cpu", "gpu"]},
        "deterministic": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "seed": {"type": "integer"},
                "max_steps": {"type": "integer"},
                "temperature": {"type": "number"},
            },
        },
    },
}


@dataclass(frozen=True)
class ProfileSpec:
    profile_id: str
    profile_version: str
    device: str
    deterministic: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "ProfileSpec":
        validate_schema(PROFILE_SCHEMA, payload)
        return cls(
            profile_id=payload["profile_id"],
            profile_version=payload["profile_version"],
            device=payload["device"],
            deterministic=dict(payload.get("deterministic", {})),
        )


def load_profile_from_path(path: Path) -> ProfileSpec:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return ProfileSpec.from_dict(payload)


def load_profile_by_id(profile_id: str) -> ProfileSpec:
    profiles_dir = _profiles_root()
    path = profiles_dir / f"{profile_id}.json"
    if not path.exists():
        raise FileNotFoundError(f"Profile not found: {profile_id}")
    profile = load_profile_from_path(path)
    if profile.profile_id != profile_id:
        raise AssertionError("Profile ID mismatch.")
    return profile


def _profiles_root() -> Path:
    return Path(__file__).resolve().parents[2] / "profiles"
