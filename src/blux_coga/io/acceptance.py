"""Acceptance harness for CogA fixtures."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from blux_coga.contracts.determinism import stable_json_dumps
from blux_coga.contracts.models import ProblemSpec
from blux_coga.contracts.processor import run_contract
from blux_coga.contracts.reasoning_packs import load_reasoning_pack
from blux_coga.contracts.schema import validate_schema
from blux_coga.core.constants import (
    CONTRACT_VERSION,
    DEFAULT_REASONING_PACK_ID,
    MODEL_VERSION,
    SCHEMA_VERSION,
)


def run_acceptance(fixtures_dir: Path, output_dir: Path) -> Dict[str, Any]:
    fixtures_dir = fixtures_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    cases: List[Dict[str, Any]] = []
    status_counts = {"COMPLETE": 0, "UNCLEAR": 0, "REFUSE": 0}
    schema_failures = 0
    expected_mismatches = 0

    base_dir = Path(__file__).resolve().parents[3]
    schemas_dir = base_dir / "schemas"
    thought_schema = json.loads(
        (schemas_dir / "thought_artifact.schema.json").read_text(encoding="utf-8")
    )
    verdict_schema = json.loads(
        (schemas_dir / "reasoning_verdict.schema.json").read_text(encoding="utf-8")
    )
    problem_schema = json.loads(
        (schemas_dir / "problem.schema.json").read_text(encoding="utf-8")
    )

    fixture_paths = sorted(fixtures_dir.glob("*.json"), key=lambda path: path.name)
    for fixture_path in fixture_paths:
        payload = json.loads(fixture_path.read_text(encoding="utf-8"))
        errors: List[str] = []
        try:
            validate_schema(problem_schema, payload)
        except AssertionError as exc:
            errors.append(f"problem_schema: {exc}")
        problem_spec = ProblemSpec.from_dict(payload)
        artifact, verdict, _state = run_contract(problem_spec)

        case_dir = output_dir / fixture_path.stem
        case_dir.mkdir(parents=True, exist_ok=True)
        artifact_path = case_dir / "thought_artifact.json"
        verdict_path = case_dir / "reasoning_verdict.json"
        artifact_path.write_text(
            stable_json_dumps(artifact.to_dict()), encoding="utf-8"
        )
        verdict_path.write_text(stable_json_dumps(verdict.to_dict()), encoding="utf-8")

        try:
            validate_schema(thought_schema, artifact.to_dict())
            validate_schema(verdict_schema, verdict.to_dict())
        except AssertionError as exc:
            errors.append(f"output_schema: {exc}")

        status_counts[verdict.status.value] += 1
        expected_dir = fixtures_dir / fixture_path.stem
        expected_artifact = expected_dir / "thought_artifact.json"
        expected_verdict = expected_dir / "reasoning_verdict.json"
        expected_matches = {"thought_artifact": None, "reasoning_verdict": None}
        if expected_artifact.exists():
            expected_payload = json.loads(
                expected_artifact.read_text(encoding="utf-8")
            )
            expected_matches["thought_artifact"] = (
                stable_json_dumps(expected_payload)
                == stable_json_dumps(artifact.to_dict())
            )
        if expected_verdict.exists():
            expected_payload = json.loads(expected_verdict.read_text(encoding="utf-8"))
            expected_matches["reasoning_verdict"] = (
                stable_json_dumps(expected_payload)
                == stable_json_dumps(verdict.to_dict())
            )
        if any(match is False for match in expected_matches.values()):
            expected_mismatches += 1
        if errors:
            schema_failures += 1
        cases.append(
            {
                "fixture": fixture_path.name,
                "input_hash": artifact.run_header.input_hash,
                "status": verdict.status.value,
                "thought_artifact": f"{fixture_path.stem}/thought_artifact.json",
                "reasoning_verdict": f"{fixture_path.stem}/reasoning_verdict.json",
                "schema_valid": not errors,
                "errors": errors,
                "expected_matches": expected_matches,
            }
        )

    packs_dir = Path(__file__).resolve().parents[3] / "reasoning_packs"
    reasoning_pack = load_reasoning_pack(DEFAULT_REASONING_PACK_ID, packs_dir)
    report = {
        "contract_version": CONTRACT_VERSION,
        "model_version": MODEL_VERSION,
        "reasoning_pack_id": reasoning_pack.pack_id,
        "reasoning_pack_version": reasoning_pack.version,
        "schema_version": SCHEMA_VERSION,
        "cases": cases,
        "summary": {
            "total": len(cases),
            "status_counts": status_counts,
            "schema_failures": schema_failures,
            "expected_mismatches": expected_mismatches,
        },
    }

    (output_dir / "report.json").write_text(
        stable_json_dumps(report), encoding="utf-8"
    )
    return report
