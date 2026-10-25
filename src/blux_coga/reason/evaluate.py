"""Regression and adversarial evaluation (`coga eval`, docs/EVALUATION.md).

A suite directory holds `suite.json`:

    {"contract": "coga.eval-suite", "version": 1, "suite_id": "...", "dataset": {"dataset_id", "version"},
     "cases": [{"id", "capability", "request": "cases/x.json", "kind": "regression" | "adversarial",
                "expect": {"artifact_id"?: hex, "error"?: CODE, "result"?: {json-pointer: value}}}]}

A case passes when the run matches every expectation: an exact artifact id (regression), an error code
(adversarial inputs that must be rejected), or selected result values (adversarial inputs that must not
move a result). Each case is a dataset record: (dataset_id, version, case id).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from blux_coga.reason.common import CogaError, parse_request
from blux_coga.reason.engine import run


def pointer(doc: Any, path: str) -> Any:
    for part in [p for p in path.split("/") if p]:
        doc = doc[int(part)] if isinstance(doc, list) else doc[part]
    return doc


def run_suite(directory: Path) -> dict[str, Any]:
    suite_path = directory / "suite.json"
    try:
        suite = json.loads(suite_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CogaError("INVALID_SUITE", f"Cannot read {suite_path}: {exc}.") from None
    if suite.get("contract") != "coga.eval-suite" or suite.get("version") != 1:
        raise CogaError("INVALID_SUITE", f"{suite_path} is not a coga.eval-suite v1 document.")
    results = []
    for case in suite["cases"]:
        expect = case["expect"]
        outcome: dict[str, Any] = {"id": case["id"], "capability": case["capability"], "kind": case["kind"]}
        try:
            request = parse_request((directory / case["request"]).read_bytes())
            artifact = run(case["capability"], request)
        except CogaError as exc:
            outcome["error"] = exc.code
            outcome["passed"] = expect.get("error") == exc.code
            if not outcome["passed"]:
                outcome["reason"] = f"unexpected error {exc.code}: {exc.message}"
            results.append(outcome)
            continue
        problems = []
        if "error" in expect:
            problems.append(f"expected error {expect['error']}, got an artifact")
        if "artifact_id" in expect and artifact["artifact_id"] != expect["artifact_id"]:
            problems.append(f"artifact_id {artifact['artifact_id']} != expected {expect['artifact_id']}")
        for path, want in sorted(expect.get("result", {}).items()):
            try:
                got = pointer(artifact, path)
            except (KeyError, IndexError, ValueError):
                got = "<missing>"
            if got != want:
                problems.append(f"{path} = {got!r}, expected {want!r}")
        outcome["artifact_id"] = artifact["artifact_id"]
        outcome["passed"] = not problems
        if problems:
            outcome["reason"] = "; ".join(problems)
        results.append(outcome)
    failed = [r for r in results if not r["passed"]]
    return {
        "contract": "coga.eval-report",
        "version": 1,
        "suite_id": suite["suite_id"],
        "dataset": suite.get("dataset"),
        "passed": len(results) - len(failed),
        "failed": len(failed),
        "verdict": "pass" if not failed else "fail",
        "cases": results,
    }
