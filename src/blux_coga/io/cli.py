"""CLI harness for BLUX CogA."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Optional

from blux_coga.contracts.determinism import stable_json_dumps
from blux_coga.contracts.models import ProblemSpec
from blux_coga.core.thinker import CogAThinker
from blux_coga.io.acceptance import run_acceptance
from blux_coga.profiles import load_profile_by_id, load_profile_from_path


def _build_run_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--input",
        "--in",
        "-i",
        dest="input",
        type=Path,
        help="Path to a ProblemSpec JSON file.",
    )
    parser.add_argument(
        "--output-dir",
        "--out",
        "-o",
        dest="output_dir",
        type=Path,
        default=Path("out"),
        help=(
            "Directory for canonical outputs. File mode writes thought_artifact.json "
            "and reasoning_verdict.json into this directory."
        ),
    )
    profile_group = parser.add_mutually_exclusive_group()
    profile_group.add_argument(
        "--profile",
        type=str,
        help="Profile id from profiles/ (for example: cpu or gpu).",
    )
    profile_group.add_argument(
        "--profile-file",
        type=Path,
        help="Path to a profile JSON file.",
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Run the optional interactive REPL instead of canonical file mode.",
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="blux-coga",
        description=(
            "Run deterministic BLUX CogA contract processing. "
            "Canonical harness usage is: blux-coga run --input problem.json --output-dir out"
        ),
    )
    subparsers = parser.add_subparsers(dest="command")

    run_parser = subparsers.add_parser(
        "run",
        help="Canonical file-based contract execution.",
    )
    _build_run_parser(run_parser)

    accept_parser = subparsers.add_parser(
        "accept",
        help="Replay acceptance fixtures and write deterministic reports.",
    )
    accept_parser.add_argument(
        "--fixtures",
        type=Path,
        required=True,
        help="Directory containing ProblemSpec fixture files.",
    )
    accept_parser.add_argument(
        "--out",
        type=Path,
        required=True,
        help="Directory for acceptance outputs.",
    )
    return parser


def _load_profile(args: argparse.Namespace) -> Optional[object]:
    if args.profile_file:
        return load_profile_from_path(args.profile_file)
    if args.profile:
        return load_profile_by_id(args.profile)
    return None


def _write_outputs(output_dir: Path, artifact, verdict) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "thought_artifact.json").write_text(
        stable_json_dumps(artifact.to_dict()), encoding="utf-8"
    )
    (output_dir / "reasoning_verdict.json").write_text(
        stable_json_dumps(verdict.to_dict()), encoding="utf-8"
    )


def _run_file_or_interactive(args: argparse.Namespace) -> None:
    profile = _load_profile(args)
    output_dir: Path = args.output_dir

    if args.interactive:
        thinker = CogAThinker(profile=profile)
        output_dir.mkdir(parents=True, exist_ok=True)
        while True:
            try:
                user_input = input("> ")
            except EOFError:
                break
            artifact, verdict = thinker.respond(user_input)
            _write_outputs(output_dir, artifact, verdict)
            print(artifact.response_text)
            if thinker.state.stopped or thinker.state.frozen:
                break
        return

    if not args.input:
        raise SystemExit(
            "Provide --input for canonical file mode or use --interactive for the REPL."
        )

    payload = json.loads(args.input.read_text(encoding="utf-8"))
    problem_spec = ProblemSpec.from_dict(payload)
    thinker = CogAThinker(problem_spec.to_session_state(), profile=profile)
    artifact, verdict = thinker.respond(problem_spec.user_input)
    _write_outputs(output_dir, artifact, verdict)


def main() -> None:
    parser = _build_parser()
    argv = sys.argv[1:]
    if not argv:
        parser.print_help()
        raise SystemExit(1)
    if argv and argv[0] not in {"run", "accept", "-h", "--help"}:
        argv = ["run", *argv]
    args = parser.parse_args(argv)

    if args.command in {None, "run"}:
        _run_file_or_interactive(args)
        return
    if args.command == "accept":
        run_acceptance(args.fixtures, args.out)
        return
    raise SystemExit(f"Unknown command: {args.command}")


if __name__ == "__main__":
    main()
