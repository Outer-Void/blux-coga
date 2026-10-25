"""Run and replay capabilities."""

from __future__ import annotations

import copy
from collections.abc import Callable
from typing import Any

from blux_coga.reason import analyze, compare, critique, decompose, plan, rank, risk
from blux_coga.reason.common import (
    ENGINE_VERSION,
    CogaError,
    Draft,
    Evidence,
    check_request,
    evidence_table,
    finish,
    schema,
    sha256_of,
    validate,
)

CAPABILITIES: dict[str, Callable[[dict[str, Any], dict[str, Evidence]], Draft]] = {
    "reason.analyze": analyze.run,
    "reason.compare": compare.run,
    "reason.critique": critique.run,
    "reason.decompose": decompose.run,
    "reason.plan": plan.run,
    "reason.rank": rank.run,
    "reason.risk": risk.run,
}


def run(capability: str, request: Any, *, linkage: dict[str, Any] | None = None) -> dict[str, Any]:
    """Validate the request against its schema, compute, and return a schema-valid coga.artifact."""
    req = check_request(capability, copy.deepcopy(request))
    ev = evidence_table(req)
    artifact = finish(capability, req, CAPABILITIES[capability](req, ev), ev)
    artifact["linkage"] = linkage
    out_schema = schema(f"{capability}.artifact.v1.json")
    errors = validate(artifact, out_schema, out_schema)
    if errors:  # pragma: no cover - a bug in CogA, never in the request
        raise CogaError(
            "INTERNAL_ERROR", f"Artifact does not satisfy its schema: {errors[0]}", details={"errors": errors}
        )
    return artifact


def replay(artifact: Any, request: Any) -> dict[str, Any]:
    """Recompute ARTIFACT from REQUEST. The recomputed artifact keeps the original linkage, so it is
    byte-identical (and hashes identically in BLUX System) when the engine reproduces the result."""
    if not isinstance(artifact, dict) or artifact.get("contract") != "coga.artifact":
        raise CogaError("INVALID_ARTIFACT", "Not a coga.artifact document.")
    capability = artifact.get("capability")
    if capability not in CAPABILITIES:
        raise CogaError("INVALID_ARTIFACT", f"Unknown capability {capability!r} in the artifact.")
    recomputed = run(capability, request, linkage=artifact.get("linkage"))
    checks = {
        "input_match": recomputed["input_sha256"] == artifact.get("input_sha256"),
        "artifact_id_match": recomputed["artifact_id"] == artifact.get("artifact_id"),
        "document_match": sha256_of(recomputed) == sha256_of(artifact),
        "same_engine": artifact.get("engine", {}).get("version") == ENGINE_VERSION,
    }
    return {
        "contract": "coga.replay",
        "version": 1,
        "capability": capability,
        "ok": checks["input_match"] and checks["artifact_id_match"] and checks["document_match"],
        "checks": checks,
        "original": {"artifact_id": artifact.get("artifact_id"), "engine": artifact.get("engine")},
        "recomputed": {"artifact_id": recomputed["artifact_id"], "engine": recomputed["engine"]},
        "artifact": recomputed,
    }
