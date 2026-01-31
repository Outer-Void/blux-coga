"""Deterministic reasoning pack loader."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from blux_coga.contracts.determinism import stable_json_dumps


@dataclass(frozen=True)
class ReasoningPack:
    pack_id: str
    version: str
    description: str

    @classmethod
    def from_dict(cls, payload: dict) -> "ReasoningPack":
        return cls(
            pack_id=str(payload.get("id", "")),
            version=str(payload.get("version", "")),
            description=str(payload.get("description", "")),
        )

    def to_dict(self) -> dict:
        return {
            "id": self.pack_id,
            "version": self.version,
            "description": self.description,
        }

    def stable_fingerprint(self) -> str:
        return stable_json_dumps(self.to_dict())


def load_reasoning_pack(pack_id: str, packs_dir: Path) -> ReasoningPack:
    pack_path = packs_dir / f"{pack_id}.json"
    payload = json.loads(pack_path.read_text(encoding="utf-8"))
    pack = ReasoningPack.from_dict(payload)
    if pack.pack_id != pack_id:
        raise ValueError("Reasoning pack id mismatch.")
    if not pack.version:
        raise ValueError("Reasoning pack version missing.")
    return pack
