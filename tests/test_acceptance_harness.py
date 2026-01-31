from pathlib import Path

from blux_coga.contracts.determinism import stable_json_dumps
from blux_coga.io.acceptance import run_acceptance


def _write_fixture(path: Path, user_input: str) -> None:
    payload = {
        "user_input": user_input,
        "session": {
            "history": [],
            "last_user_utterances": [],
            "last_intent": None,
            "extracted_intent": None,
            "extracted_constraints": [],
            "stopped": False,
            "frozen": False,
        },
    }
    path.write_text(stable_json_dumps(payload), encoding="utf-8")


def test_acceptance_harness_determinism(tmp_path: Path) -> None:
    fixtures = tmp_path / "fixtures"
    fixtures.mkdir()
    _write_fixture(fixtures / "case_a.json", "I might stay or go.")
    _write_fixture(fixtures / "case_b.json", "Summarize")

    out_one = tmp_path / "out_one"
    out_two = tmp_path / "out_two"

    report_one = run_acceptance(fixtures, out_one)
    report_two = run_acceptance(fixtures, out_two)

    assert stable_json_dumps(report_one) == stable_json_dumps(report_two)
    assert (out_one / "report.json").read_text(encoding="utf-8") == (
        out_two / "report.json"
    ).read_text(encoding="utf-8")

    for case in report_one["cases"]:
        artifact_path = case["thought_artifact"]
        verdict_path = case["reasoning_verdict"]
        assert (out_one / artifact_path).read_text(encoding="utf-8") == (
            out_two / artifact_path
        ).read_text(encoding="utf-8")
        assert (out_one / verdict_path).read_text(encoding="utf-8") == (
            out_two / verdict_path
        ).read_text(encoding="utf-8")
