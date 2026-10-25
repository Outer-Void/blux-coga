"""Shared machinery for the CogA 2 reasoning engine: request validation, evidence, artifacts, replay hashing.

Determinism rules (docs/REASONING.md#determinism): inputs are processed in id order, arithmetic is limited to
+, -, *, / (no libm functions whose last bits differ between platforms), every float in an artifact is rounded
to 6 decimals, and the artifact id is the SHA-256 of the canonical artifact without its linkage.
Free text (claims, titles, questions) is carried, never interpreted: it cannot change a result.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import dataclass, field
from functools import cache
from importlib import resources
from typing import Any

ENGINE_NAME = "coga"
ENGINE_VERSION = "2.0.0"
ALGORITHMS = {
    "reason.analyze": "1",
    "reason.compare": "1",
    "reason.critique": "1",
    "reason.decompose": "1",
    "reason.plan": "1",
    "reason.rank": "1",
    "reason.risk": "1",
}
MAX_REQUEST_BYTES = 2 * 1024 * 1024
DEFAULT_RELIABILITY = {
    "measurement": 0.9,
    "observation": 0.8,
    "dataset": 0.8,
    "document": 0.7,
    "testimony": 0.5,
    "assumption": 0.3,
}


class CogaError(Exception):
    """The request cannot be reasoned about (structure, references, limits). Never a finding."""

    def __init__(self, code: str, message: str, *, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = dict(details or {})

    def to_dict(self) -> dict[str, Any]:
        return {"code": self.code, "message": self.message, "details": self.details}


def r6(x: float) -> float:
    """Round for output. -0.0 becomes 0.0 so equal values have one spelling."""
    y = round(x, 6)
    return 0.0 if y == 0 else y


def canonical(doc: Any) -> str:
    return json.dumps(doc, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def sha256_of(doc: Any) -> str:
    return hashlib.sha256(canonical(doc).encode("utf-8")).hexdigest()


def _reject_constant(name: str) -> Any:
    raise CogaError("INVALID_REQUEST", f"Non-finite number {name} is not allowed.")


def _no_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for k, v in pairs:
        if k in out:
            raise CogaError("INVALID_REQUEST", f"Duplicate JSON key {k!r}.")
        out[k] = v
    return out


def parse_request(raw: bytes | str) -> Any:
    data = raw.encode("utf-8") if isinstance(raw, str) else raw
    if len(data) > MAX_REQUEST_BYTES:
        raise CogaError("LIMIT_EXCEEDED", f"Request larger than {MAX_REQUEST_BYTES} bytes.")
    try:
        return json.loads(data, object_pairs_hook=_no_duplicates, parse_constant=_reject_constant)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CogaError("INVALID_REQUEST", f"Request is not JSON: {exc}.") from None


# ----------------------------------------------------------------------------------------------- schemas


@cache
def schema(name: str) -> dict[str, Any]:
    text = resources.files("blux_coga.reason").joinpath("schemas").joinpath(name).read_text(encoding="utf-8")
    return json.loads(text)  # type: ignore[no-any-return]


_TYPES = {
    "object": lambda v: isinstance(v, dict),
    "array": lambda v: isinstance(v, list),
    "string": lambda v: isinstance(v, str),
    "integer": lambda v: isinstance(v, int) and not isinstance(v, bool),
    "number": lambda v: isinstance(v, (int, float)) and not isinstance(v, bool),
    "boolean": lambda v: isinstance(v, bool),
    "null": lambda v: v is None,
}


def validate(value: Any, sch: dict[str, Any], root: dict[str, Any], path: str = "$") -> list[str]:
    """The JSON Schema 2020-12 subset CogA's schemas use. Returns error strings ("path: problem")."""
    if "$ref" in sch:
        ref = sch["$ref"]
        if not ref.startswith("#/$defs/"):
            return [f"{path}: unsupported $ref {ref}"]
        return validate(value, root["$defs"][ref.removeprefix("#/$defs/")], root, path)
    errs: list[str] = []
    if "const" in sch and value != sch["const"]:
        return [f"{path}: must be {sch['const']!r}"]
    if "enum" in sch and value not in sch["enum"]:
        return [f"{path}: must be one of {sch['enum']}"]
    if "type" in sch:
        types = sch["type"] if isinstance(sch["type"], list) else [sch["type"]]
        if not any(_TYPES[t](value) for t in types):
            return [f"{path}: must be {' or '.join(types)}"]
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if isinstance(value, float) and not math.isfinite(value):
            return [f"{path}: must be finite"]
        if "minimum" in sch and value < sch["minimum"]:
            errs.append(f"{path}: must be >= {sch['minimum']}")
        if "maximum" in sch and value > sch["maximum"]:
            errs.append(f"{path}: must be <= {sch['maximum']}")
        if "exclusiveMinimum" in sch and value <= sch["exclusiveMinimum"]:
            errs.append(f"{path}: must be > {sch['exclusiveMinimum']}")
    if isinstance(value, str):
        if "minLength" in sch and len(value) < sch["minLength"]:
            errs.append(f"{path}: shorter than {sch['minLength']}")
        if "maxLength" in sch and len(value) > sch["maxLength"]:
            errs.append(f"{path}: longer than {sch['maxLength']}")
        if "pattern" in sch and not re.search(sch["pattern"], value):
            errs.append(f"{path}: does not match {sch['pattern']}")
    if isinstance(value, list):
        if "minItems" in sch and len(value) < sch["minItems"]:
            errs.append(f"{path}: needs at least {sch['minItems']} items")
        if "maxItems" in sch and len(value) > sch["maxItems"]:
            return [f"{path}: more than {sch['maxItems']} items"]
        if sch.get("uniqueItems") and len({canonical(v) for v in value}) != len(value):
            errs.append(f"{path}: items must be unique")
        if "items" in sch:
            for i, item in enumerate(value):
                errs.extend(validate(item, sch["items"], root, f"{path}[{i}]"))
    if isinstance(value, dict):
        props = sch.get("properties", {})
        for key in sch.get("required", []):
            if key not in value:
                errs.append(f"{path}: missing {key!r}")
        if "maxProperties" in sch and len(value) > sch["maxProperties"]:
            return [f"{path}: more than {sch['maxProperties']} properties"]
        extra = sch.get("additionalProperties", True)
        for key in sorted(value):
            sub = f"{path}.{key}"
            if key in props:
                errs.extend(validate(value[key], props[key], root, sub))
            elif extra is False:
                errs.append(f"{path}: unknown property {key!r}")
            elif isinstance(extra, dict):
                errs.extend(validate(value[key], extra, root, sub))
    return errs


def check_request(capability: str, request: Any) -> dict[str, Any]:
    if capability not in ALGORITHMS:
        raise CogaError(
            "UNKNOWN_CAPABILITY", f"Unknown capability {capability!r}.", details={"known": sorted(ALGORITHMS)}
        )
    sch = schema(f"{capability}.request.v1.json")
    errors = validate(request, sch, sch)
    if errors:
        raise CogaError(
            "INVALID_REQUEST",
            f"Request does not satisfy the {capability} request schema: {errors[0]}"
            + (f" (and {len(errors) - 1} more)" if len(errors) > 1 else ""),
            details={"errors": errors[:50]},
        )
    return request  # type: ignore[no-any-return]


# ----------------------------------------------------------------------------------------------- evidence


@dataclass(frozen=True)
class Evidence:
    id: str
    kind: str
    reliability: float
    uri: str | None
    dataset: dict[str, str] | None
    sha256: str | None


def evidence_table(request: dict[str, Any]) -> dict[str, Evidence]:
    table: dict[str, Evidence] = {}
    for i, e in enumerate(request.get("evidence", [])):
        if e["id"] in table:
            raise CogaError(
                "DUPLICATE_ID", f"Evidence id {e['id']!r} appears twice.", details={"path": f"$.evidence[{i}]"}
            )
        kind = e.get("kind", "document")
        source = e.get("source", {})
        table[e["id"]] = Evidence(
            id=e["id"],
            kind=kind,
            reliability=float(e.get("reliability", DEFAULT_RELIABILITY[kind])),
            uri=source.get("uri"),
            dataset=source.get("dataset"),
            sha256=source.get("sha256"),
        )
    return table


def unique_ids(rows: list[dict[str, Any]], what: str, key: str = "id") -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for i, row in enumerate(rows):
        if row[key] in out:
            raise CogaError("DUPLICATE_ID", f"{what} id {row[key]!r} appears twice.", details={"index": i})
        out[row[key]] = row
    return out


def require_refs(refs: list[str], known: dict[str, Any], what: str, where: str) -> None:
    missing = [r for r in refs if r not in known]
    if missing:
        raise CogaError(
            "UNKNOWN_REFERENCE",
            f"{where} refers to unknown {what} {', '.join(repr(m) for m in missing[:5])}.",
            details={"where": where, "missing": missing[:50]},
        )


def noisy_or(probabilities: list[float]) -> float:
    """P(at least one is right), treating sources as independent. Order-independent up to float rounding;
    callers pass values in id order so results are reproducible."""
    miss = 1.0
    for p in probabilities:
        miss *= 1.0 - p
    return 1.0 - miss


def find_cycle(nodes: list[str], edges: dict[str, list[str]]) -> list[str] | None:
    """The first cycle in id order (deterministic), as [a, b, ..., a], or None."""
    state: dict[str, int] = {}
    stack: list[str] = []

    def visit(n: str) -> list[str] | None:
        state[n] = 1
        stack.append(n)
        for m in sorted(edges.get(n, [])):
            if state.get(m) == 1:
                return [*stack[stack.index(m) :], m]
            if m not in state:
                found = visit(m)
                if found:
                    return found
        stack.pop()
        state[n] = 2
        return None

    for n in sorted(nodes):
        if n not in state:
            found = visit(n)
            if found:
                return found
    return None


def topo_order(nodes: list[str], deps: dict[str, list[str]]) -> list[str]:
    """Kahn's algorithm; among ready nodes the smallest id goes first. Assumes no cycle."""
    remaining = {n: set(deps.get(n, [])) for n in nodes}
    order: list[str] = []
    while remaining:
        ready = sorted(n for n, d in remaining.items() if not d)
        n = ready[0]
        order.append(n)
        del remaining[n]
        for d in remaining.values():
            d.discard(n)
    return order


# ----------------------------------------------------------------------------------------------- artifacts


@dataclass
class Draft:
    """What a capability computes. `finish` turns it into a coga.artifact."""

    result: dict[str, Any]
    confidence: float
    confidence_basis: str
    evidence_refs: set[str] = field(default_factory=set)
    uncertainty: list[dict[str, Any]] = field(default_factory=list)
    findings: list[dict[str, Any]] = field(default_factory=list)

    def gap(self, code: str, message: str, refs: list[str] | None = None) -> None:
        self.uncertainty.append({"code": code, "message": message, "refs": sorted(refs or [])})

    def note(self, code: str, message: str, refs: list[str] | None = None, severity: str = "low") -> None:
        self.findings.append({"code": code, "message": message, "refs": sorted(refs or []), "severity": severity})


def uncertainty_level(confidence: float, sources: list[dict[str, Any]]) -> str:
    if confidence >= 0.7 and len(sources) <= 1:
        return "low"
    if confidence >= 0.4:
        return "medium"
    return "high"


def _round_floats(value: Any) -> Any:
    if isinstance(value, float):
        return r6(value)
    if isinstance(value, dict):
        return {k: _round_floats(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_round_floats(v) for v in value]
    return value


def finish(capability: str, request: dict[str, Any], draft: Draft, evidence: dict[str, Evidence]) -> dict[str, Any]:
    input_sha = sha256_of(request)
    datasets = sorted(
        (
            {**dict(e.dataset), "evidence_id": e.id}
            for e in evidence.values()
            if e.dataset and e.id in draft.evidence_refs
        ),
        key=lambda d: (d["dataset_id"], d["version"], d["record_id"], d["evidence_id"]),
    )
    sources = sorted(draft.uncertainty, key=lambda s: (s["code"], s["refs"], s["message"]))
    confidence = r6(min(1.0, max(0.0, draft.confidence)))
    body: dict[str, Any] = _round_floats(
        {
            "contract": "coga.artifact",
            "version": 1,
            "engine": {
                "name": ENGINE_NAME,
                "version": ENGINE_VERSION,
                "algorithm": f"{capability}/{ALGORITHMS[capability]}",
                "deterministic": True,
            },
            "capability": capability,
            "input_sha256": input_sha,
            "question": request.get("question"),
            "result": draft.result,
            "evidence_refs": sorted(draft.evidence_refs),
            "confidence": {"value": confidence, "basis": draft.confidence_basis},
            "uncertainty": {"level": uncertainty_level(confidence, sources), "sources": sources},
            "findings": sorted(draft.findings, key=lambda f: (f["code"], f["refs"], f["message"])),
            "dataset": datasets,
        }
    )
    artifact_id = sha256_of(body)
    body["artifact_id"] = artifact_id
    body["replay"] = {
        "engine_version": ENGINE_VERSION,
        "algorithm": body["engine"]["algorithm"],
        "input_sha256": input_sha,
        "artifact_id": artifact_id,
        "deterministic": True,
        "command": f"coga replay ARTIFACT.json --request REQUEST.json  # {capability}",
    }
    body["linkage"] = None
    return body
