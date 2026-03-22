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


def test_single_turn_interactive_matches_file_mode(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, problem_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    file_out = tmp_path / "file-out"
    interactive_out = tmp_path / "interactive-out"

    monkeypatch.setattr(
        sys,
        "argv",
        ["blux-coga", "run", "--input", str(problem_path), "--output-dir", str(file_out)],
    )
    cli.main()

    responses = iter(["I might stay or go."])

    def fake_input(_prompt: str) -> str:
        try:
            return next(responses)
        except StopIteration as exc:
            raise EOFError from exc

    monkeypatch.setattr("builtins.input", fake_input)
    monkeypatch.setattr(
        sys,
        "argv",
        ["blux-coga", "run", "--interactive", "--output-dir", str(interactive_out)],
    )
    cli.main()
    capsys.readouterr()

    assert (file_out / "thought_artifact.json").read_text(encoding="utf-8") == (
        interactive_out / "thought_artifact.json"
    ).read_text(encoding="utf-8")
    assert (file_out / "reasoning_verdict.json").read_text(encoding="utf-8") == (
        interactive_out / "reasoning_verdict.json"
    ).read_text(encoding="utf-8")


def test_accept_subcommand_supports_canonical_output_dir_alias() -> None:
    parser = cli._build_parser()
    args = parser.parse_args(
        ["accept", "--fixtures", "fixtures", "--output-dir", "accept-out"]
    )

    assert str(args.fixtures) == "fixtures"
    assert str(args.output_dir) == "accept-out"
