from __future__ import annotations

import json
from pathlib import Path

from blux_coga.contracts.determinism import stable_json_dumps
from blux_coga.io.acceptance import run_acceptance


FIXTURES_DIR = Path("tests/fixtures/live_dataset_cases")
EXPECTED_DIR = Path("tests/fixtures/live_dataset_cases_expected")


def _load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_live_dataset_fixture_replay_matches_frozen_expectations(tmp_path: Path) -> None:
    out_dir = tmp_path / "out"
    report = run_acceptance(FIXTURES_DIR, out_dir)

    for case in report["cases"]:
        stem = Path(case["fixture"]).stem
        for filename in ("thought_artifact.json", "reasoning_verdict.json"):
            expected_path = EXPECTED_DIR / stem / filename
            actual_path = out_dir / stem / filename
            assert stable_json_dumps(_load_json(actual_path)) == stable_json_dumps(
                _load_json(expected_path)
            )


def test_live_dataset_fixture_replay_is_repeatable(tmp_path: Path) -> None:
    out_one = tmp_path / "out_one"
    out_two = tmp_path / "out_two"

    report_one = run_acceptance(FIXTURES_DIR, out_one)
    report_two = run_acceptance(FIXTURES_DIR, out_two)

    assert stable_json_dumps(report_one) == stable_json_dumps(report_two)

    for case in report_one["cases"]:
        stem = Path(case["fixture"]).stem
        for filename in ("thought_artifact.json", "reasoning_verdict.json"):
            assert (out_one / stem / filename).read_text(encoding="utf-8") == (
                out_two / stem / filename
            ).read_text(encoding="utf-8")
