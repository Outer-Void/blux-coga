"""CogA 2 reasoning engine: explicit, deterministic reasoning structures for BLUX (docs/REASONING.md).

Every capability turns a structured `coga.request` into a `coga.artifact`: computed results, the evidence
they rest on, a confidence value with its basis, the sources of uncertainty, and replay metadata. Artifacts
are BLUX-owned reasoning structures. They are not, and never contain, a model's hidden chain-of-thought:
no model is involved at all.
"""

from blux_coga.reason.common import ALGORITHMS, ENGINE_VERSION, CogaError
from blux_coga.reason.engine import CAPABILITIES, replay, run

__all__ = ["ALGORITHMS", "CAPABILITIES", "ENGINE_VERSION", "CogaError", "replay", "run"]
