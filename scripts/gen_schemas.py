#!/usr/bin/env python3
"""Generate CogA 2 JSON Schemas (src/blux_coga/reason/schemas/) and .blux/capabilities.yaml from one source.

python scripts/gen_schemas.py          # write
python scripts/gen_schemas.py --check  # exit 1 if the committed files differ (CI)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "src" / "blux_coga" / "reason" / "schemas"
ENGINE_VERSION = "2.0.0"
D = "https://json-schema.org/draft/2020-12/schema"

ID = {"type": "string", "pattern": "^[A-Za-z0-9][A-Za-z0-9_.:-]{0,63}$"}
TEXT = {"type": "string", "maxLength": 4000}
IDS = {"type": "array", "maxItems": 1000, "uniqueItems": True, "items": {"$ref": "#/$defs/id"}}
UNIT = {"type": "number", "minimum": 0, "maximum": 1}
HEX64 = {"type": "string", "pattern": "^[0-9a-f]{64}$"}

DEFS: dict[str, Any] = {
    "id": ID,
    "text": TEXT,
    "ids": IDS,
    "unit": UNIT,
    "evidence": {
        "type": "object",
        "additionalProperties": False,
        "required": ["id", "claim"],
        "properties": {
            "id": {"$ref": "#/$defs/id"},
            "claim": {"$ref": "#/$defs/text"},
            "kind": {"enum": ["observation", "measurement", "document", "testimony", "assumption", "dataset"]},
            "reliability": {"$ref": "#/$defs/unit"},
            "as_of": {"type": "string", "maxLength": 64},
            "source": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "uri": {"type": "string", "maxLength": 2048},
                    "sha256": HEX64,
                    "dataset": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": ["dataset_id", "version", "record_id"],
                        "properties": {
                            "dataset_id": {"type": "string", "pattern": "^[a-z0-9][a-z0-9_.-]{0,127}$"},
                            "version": {"type": "string", "minLength": 1, "maxLength": 64},
                            "record_id": {"type": "string", "minLength": 1, "maxLength": 256},
                            "sha256": HEX64,
                        },
                    },
                },
            },
        },
    },
    "claim": {
        "type": "object",
        "additionalProperties": False,
        "required": ["id", "statement"],
        "properties": {
            "id": {"$ref": "#/$defs/id"},
            "statement": {"$ref": "#/$defs/text"},
            "supported_by": {"$ref": "#/$defs/ids"},
            "contradicted_by": {"$ref": "#/$defs/ids"},
            "depends_on": {"$ref": "#/$defs/ids"},
        },
    },
    "task": {
        "type": "object",
        "additionalProperties": False,
        "required": ["id", "title"],
        "properties": {
            "id": {"$ref": "#/$defs/id"},
            "title": {"$ref": "#/$defs/text"},
            "depends_on": {"$ref": "#/$defs/ids"},
            "effort": {"type": "number", "minimum": 0, "maximum": 1000000},
            "evidence": {"$ref": "#/$defs/ids"},
        },
    },
    "option": {
        "type": "object",
        "additionalProperties": False,
        "required": ["id", "title"],
        "properties": {
            "id": {"$ref": "#/$defs/id"},
            "title": {"$ref": "#/$defs/text"},
            "values": {
                "type": "object",
                "maxProperties": 100,
                "additionalProperties": {"type": ["number", "null"], "minimum": -1e12, "maximum": 1e12},
            },
            "evidence": {"type": "object", "maxProperties": 100, "additionalProperties": {"$ref": "#/$defs/ids"}},
        },
    },
    "criterion": {
        "type": "object",
        "additionalProperties": False,
        "required": ["id", "weight", "direction"],
        "properties": {
            "id": {"$ref": "#/$defs/id"},
            "title": {"$ref": "#/$defs/text"},
            "weight": {"type": "number", "exclusiveMinimum": 0, "maximum": 1000000},
            "direction": {"enum": ["max", "min"]},
        },
    },
}


def items(ref: str, max_items: int = 1000, min_items: int = 0) -> dict[str, Any]:
    return {"type": "array", "minItems": min_items, "maxItems": max_items, "items": {"$ref": f"#/$defs/{ref}"}}


BASE = {
    "contract": {"const": "coga.request"},
    "version": {"const": 1},
    "question": {"$ref": "#/$defs/text"},
    "evidence": items("evidence"),
}

REQUESTS: dict[str, tuple[str, dict[str, Any], list[str]]] = {
    "reason.analyze": (
        "Weigh each claim's supporting and contradicting evidence; propagate through claim dependencies.",
        {"claims": items("claim", min_items=1)},
        ["claims"],
    ),
    "reason.plan": (
        "Order tasks by dependency: stages, critical path, earliest/latest schedule and slack.",
        {
            "goal": {
                "type": "object",
                "additionalProperties": False,
                "required": ["statement"],
                "properties": {"id": {"$ref": "#/$defs/id"}, "statement": {"$ref": "#/$defs/text"}},
            },
            "tasks": items("task", min_items=1),
            "max_parallel": {"type": "integer", "minimum": 1, "maximum": 1000},
        },
        ["tasks"],
    ),
    "reason.compare": (
        "Weighted multi-criteria comparison: normalized matrix, totals, Pareto front, dominance, weight sensitivity.",
        {"options": items("option", min_items=1), "criteria": items("criterion", 100, 1)},
        ["options", "criteria"],
    ),
    "reason.decompose": (
        "Structure a goal into a work tree: depth, leaves, work packages, acceptance coverage and untraced items.",
        {
            "goal": {
                "type": "object",
                "additionalProperties": False,
                "required": ["statement"],
                "properties": {
                    "id": {"$ref": "#/$defs/id"},
                    "statement": {"$ref": "#/$defs/text"},
                    "acceptance": {
                        "type": "array",
                        "maxItems": 1000,
                        "items": {
                            "type": "object",
                            "additionalProperties": False,
                            "required": ["id", "statement"],
                            "properties": {
                                "id": {"$ref": "#/$defs/id"},
                                "statement": {"$ref": "#/$defs/text"},
                                "covered_by": {"$ref": "#/$defs/ids"},
                            },
                        },
                    },
                },
            },
            "items": {
                "type": "array",
                "minItems": 1,
                "maxItems": 1000,
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["id", "statement"],
                    "properties": {
                        "id": {"$ref": "#/$defs/id"},
                        "statement": {"$ref": "#/$defs/text"},
                        "parent": {"$ref": "#/$defs/id"},
                        "depends_on": {"$ref": "#/$defs/ids"},
                    },
                },
            },
        },
        ["goal", "items"],
    ),
    "reason.critique": (
        "Rule-based critique of an argument or plan: unsupported, circular, contradicted, single-source and more.",
        {
            "claims": items("claim"),
            "tasks": items("task"),
            "options": items("option"),
            "criteria": items("criterion", 100),
        },
        [],
    ),
    "reason.rank": (
        "Rank items from scores or pairwise preferences (Copeland), with ties, margins and preference cycles.",
        {
            "items": {
                "type": "array",
                "minItems": 1,
                "maxItems": 1000,
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["id"],
                    "properties": {
                        "id": {"$ref": "#/$defs/id"},
                        "title": {"$ref": "#/$defs/text"},
                        "score": {"type": "number", "minimum": -1e12, "maximum": 1e12},
                        "evidence": {"$ref": "#/$defs/ids"},
                    },
                },
            },
            "comparisons": {
                "type": "array",
                "maxItems": 10000,
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["winner", "loser"],
                    "properties": {
                        "winner": {"$ref": "#/$defs/id"},
                        "loser": {"$ref": "#/$defs/id"},
                        "weight": {"type": "number", "exclusiveMinimum": 0, "maximum": 1000000},
                        "evidence": {"$ref": "#/$defs/ids"},
                    },
                },
            },
        },
        ["items"],
    ),
    "reason.risk": (
        "Inherent and residual risk (likelihood x impact), mitigation effect, bands, appetite and evidence gaps.",
        {
            "risks": {
                "type": "array",
                "minItems": 1,
                "maxItems": 1000,
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["id", "title", "likelihood", "impact"],
                    "properties": {
                        "id": {"$ref": "#/$defs/id"},
                        "title": {"$ref": "#/$defs/text"},
                        "likelihood": {"$ref": "#/$defs/unit"},
                        "impact": {"type": "number", "minimum": 0, "maximum": 5},
                        "evidence": {"$ref": "#/$defs/ids"},
                        "mitigations": {
                            "type": "array",
                            "maxItems": 100,
                            "items": {
                                "type": "object",
                                "additionalProperties": False,
                                "required": ["id", "reduction", "applies_to"],
                                "properties": {
                                    "id": {"$ref": "#/$defs/id"},
                                    "title": {"$ref": "#/$defs/text"},
                                    "reduction": {"$ref": "#/$defs/unit"},
                                    "applies_to": {"enum": ["likelihood", "impact"]},
                                    "evidence": {"$ref": "#/$defs/ids"},
                                },
                            },
                        },
                    },
                },
            },
            "appetite": {"type": "number", "minimum": 0, "maximum": 5},
        },
        ["risks"],
    ),
}

ARTIFACT_REQUIRED = [
    "contract",
    "version",
    "engine",
    "capability",
    "artifact_id",
    "input_sha256",
    "result",
    "evidence_refs",
    "confidence",
    "uncertainty",
    "findings",
    "dataset",
    "replay",
    "linkage",
]


def request_schema(cap: str) -> dict[str, Any]:
    summary, props, required = REQUESTS[cap]
    return {
        "$schema": D,
        "$id": f"urn:outervoid:coga:{cap}:request:v1",
        "title": f"{cap} request (coga.request v1)",
        "description": summary,
        "type": "object",
        "additionalProperties": False,
        "required": ["contract", "version", *required],
        "properties": {**BASE, **props},
        "$defs": DEFS,
    }


def artifact_schema(cap: str | None = None) -> dict[str, Any]:
    issue = {
        "type": "object",
        "required": ["code", "message"],
        "properties": {
            "code": {"type": "string"},
            "message": {"type": "string"},
            "refs": {"type": "array", "items": {"type": "string"}},
            "severity": {"enum": ["low", "medium", "high"]},
        },
    }
    return {
        "$schema": D,
        "$id": f"urn:outervoid:coga:{cap or 'any'}:artifact:v1",
        "title": f"coga.artifact v1{' for ' + cap if cap else ''}",
        "description": "An explicit, deterministic reasoning structure; never hidden chain-of-thought.",
        "type": "object",
        "additionalProperties": False,
        "required": ARTIFACT_REQUIRED,
        "properties": {
            "contract": {"const": "coga.artifact"},
            "version": {"const": 1},
            "engine": {
                "type": "object",
                "additionalProperties": False,
                "required": ["name", "version", "algorithm", "deterministic"],
                "properties": {
                    "name": {"const": "coga"},
                    "version": {"type": "string"},
                    "algorithm": {"type": "string", "pattern": "^reason\\.[a-z]+/[0-9]+$"},
                    "deterministic": {"const": True},
                },
            },
            "capability": {"const": cap} if cap else {"enum": sorted(REQUESTS)},
            "artifact_id": HEX64,
            "input_sha256": HEX64,
            "question": {"type": ["string", "null"]},
            "result": {"type": "object"},
            "evidence_refs": {"type": "array", "items": {"type": "string"}},
            "confidence": {
                "type": "object",
                "additionalProperties": False,
                "required": ["value", "basis"],
                "properties": {"value": UNIT, "basis": {"type": "string"}},
            },
            "uncertainty": {
                "type": "object",
                "additionalProperties": False,
                "required": ["level", "sources"],
                "properties": {
                    "level": {"enum": ["low", "medium", "high"]},
                    "sources": {"type": "array", "items": issue},
                },
            },
            "findings": {"type": "array", "items": issue},
            "dataset": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["dataset_id", "version", "record_id", "evidence_id"],
                    "properties": {"dataset_id": {"type": "string"}, "record_id": {"type": "string"}},
                },
            },
            "replay": {
                "type": "object",
                "required": ["engine_version", "algorithm", "input_sha256", "artifact_id", "deterministic"],
                "properties": {"deterministic": {"const": True}},
            },
            "linkage": {"type": ["object", "null"]},
        },
    }


def _blux_yaml(schemas: dict[str, Any]) -> str:
    def js(d: Any) -> str:
        return json.dumps(d, separators=(",", ":"), sort_keys=True)

    lines = [
        "# GENERATED by scripts/gen_schemas.py; do not edit. CogA reasoning capabilities for BLUX (docs/BLUX.md).",
        "# Every capability is deterministic and side-effect free: input in, coga.artifact out.",
        "contract: blux.capability-set",
        'contract_version: "1.0"',
        "capabilities:",
    ]
    for cap in sorted(REQUESTS):
        summary = REQUESTS[cap][0]
        lines += [
            "  - contract: blux.capability",
            '    contract_version: "1.0"',
            f"    capability_id: {cap}",
            f"    version: {ENGINE_VERSION}",
            f"    summary: {json.dumps(summary)}",
            '    contract_versions: ["1.0"]',
            f"    input_schema: {js(schemas[f'{cap}.request.v1.json'])}",
            f"    output_schema: {js(schemas[f'{cap}.artifact.v1.json'])}",
            "    side_effects: none",
            "    required_permissions: []",
            "    idempotent: true",
            "    timeout_ms: 60000",
            "    provider:",
            "      repository: Outer-Void/blux-coga",
            "      kind: subprocess",
            f"      entrypoint: coga blux-capability {cap}",
            "    labels:",
            "      authority: deterministic",
            "      engine: coga-2",
        ]
    return "\n".join(lines) + "\n"


def generate() -> dict[Path, str]:
    schemas: dict[str, Any] = {}
    for cap in sorted(REQUESTS):
        schemas[f"{cap}.request.v1.json"] = request_schema(cap)
        schemas[f"{cap}.artifact.v1.json"] = artifact_schema(cap)
    schemas["artifact.v1.json"] = artifact_schema()
    out = {OUT / name: json.dumps(doc, indent=2, sort_keys=True) + "\n" for name, doc in schemas.items()}
    out[ROOT / ".blux" / "capabilities.yaml"] = _blux_yaml(schemas)
    return out


def main() -> int:
    files = generate()
    if "--check" in sys.argv:
        stale = [str(p.relative_to(ROOT)) for p, text in files.items() if not p.exists() or p.read_text() != text]
        if stale:
            print("stale generated files: " + ", ".join(stale), file=sys.stderr)
            return 1
        return 0
    for path, text in files.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
