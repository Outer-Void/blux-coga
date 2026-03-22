from pathlib import Path
import sys

import pytest

from blux_coga.contracts.determinism import stable_json_dumps
from blux_coga.io import cli


@pytest.fixture()
def problem_path(tmp_path: Path) -> Path:
    payload = {
        "user_input": "I might stay or go.",
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
    path = tmp_path / "problem.json"
    path.write_text(stable_json_dumps(payload), encoding="utf-8")
    return path


def test_cli_run_subcommand_writes_canonical_outputs(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, problem_path: Path
) -> None:
    out_dir = tmp_path / "out"
    monkeypatch.setattr(
        sys,
        "argv",
        ["blux-coga", "run", "--input", str(problem_path), "--output-dir", str(out_dir)],
    )
    cli.main()
    assert (out_dir / "thought_artifact.json").exists()
    assert (out_dir / "reasoning_verdict.json").exists()


def test_cli_legacy_alias_maps_to_run(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, problem_path: Path
) -> None:
    out_dir = tmp_path / "legacy-out"
    monkeypatch.setattr(
        sys,
        "argv",
        ["blux-coga", "--input", str(problem_path), "--output-dir", str(out_dir)],
    )
    cli.main()
    assert (out_dir / "thought_artifact.json").exists()
    assert (out_dir / "reasoning_verdict.json").exists()
