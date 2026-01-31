"""Acceptance harness for CogA fixtures."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from blux_coga.contracts.determinism import stable_json_dumps
from blux_coga.contracts.models import ProblemSpec
from blux_coga.contracts.processor import run_contract
from blux_coga.core.constants import CONTRACT_VERSION, MODEL_VERSION


def run_acceptance(fixtures_dir: Path, output_dir: Path) -> Dict[str, Any]:
    fixtures_dir = fixtures_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    cases: List[Dict[str, Any]] = []
    status_counts = {"COMPLETE": 0, "UNCLEAR": 0, "REFUSE": 0}

    fixture_paths = sorted(fixtures_dir.glob("*.json"), key=lambda path: path.name)
    for fixture_path in fixture_paths:
        payload = json.loads(fixture_path.read_text(encoding="utf-8"))
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

        status_counts[verdict.status.value] += 1
        cases.append(
            {
                "fixture": fixture_path.name,
                "input_hash": artifact.run_header.input_hash,
                "status": verdict.status.value,
                "thought_artifact": f"{fixture_path.stem}/thought_artifact.json",
                "reasoning_verdict": f"{fixture_path.stem}/reasoning_verdict.json",
            }
        )

    report = {
        "contract_version": CONTRACT_VERSION,
        "model_version": MODEL_VERSION,
        "cases": cases,
        "summary": {
            "total": len(cases),
            "status_counts": status_counts,
        },
    }

    (output_dir / "report.json").write_text(
        stable_json_dumps(report), encoding="utf-8"
    )
    return report
