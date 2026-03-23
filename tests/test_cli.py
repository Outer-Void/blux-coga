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


def test_parser_rejects_legacy_top_level_alias() -> None:
    parser = cli._build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["--input", "problem.json", "--output-dir", "out"])


def test_parser_rejects_legacy_short_flag_aliases() -> None:
    parser = cli._build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["run", "--in", "problem.json", "--out", "out"])


def test_accept_subcommand_requires_canonical_output_dir_flag() -> None:
    parser = cli._build_parser()
    args = parser.parse_args(
        ["accept", "--fixtures", "fixtures", "--output-dir", "accept-out"]
    )

    assert str(args.fixtures) == "fixtures"
    assert str(args.output_dir) == "accept-out"


def test_accept_subcommand_rejects_legacy_output_dir_alias() -> None:
    parser = cli._build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["accept", "--fixtures", "fixtures", "--out", "accept-out"])
