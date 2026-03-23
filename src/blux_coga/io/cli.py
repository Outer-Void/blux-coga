"""CLI harness for BLUX CogA."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Optional

from blux_coga.contracts.determinism import stable_json_dumps
from blux_coga.core.constants import PACKAGE_NAME, PACKAGE_VERSION
from blux_coga.contracts.models import ProblemSpec
from blux_coga.core.thinker import CogAThinker
from blux_coga.io.acceptance import run_acceptance
from blux_coga.profiles import load_profile_by_id, load_profile_from_path


CANONICAL_RUN_USAGE = "blux-coga run --input problem.json --output-dir out"


def _build_run_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--input",
        dest="input",
        type=Path,
        required=True,
        help="Path to a ProblemSpec JSON file.",
    )
    parser.add_argument(
        "--output-dir",
        dest="output_dir",
        type=Path,
        required=True,
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


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=PACKAGE_NAME,
        allow_abbrev=False,
        description=(
            f"Run deterministic BLUX CogA contract processing for {PACKAGE_NAME} {PACKAGE_VERSION}. "
            f"Canonical harness usage is: {CANONICAL_RUN_USAGE}"
        ),
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser(
        "run",
        help="Canonical file-based contract execution.",
        allow_abbrev=False,
    )
    _build_run_parser(run_parser)

    accept_parser = subparsers.add_parser(
        "accept",
        help="Replay acceptance fixtures and write deterministic reports.",
        allow_abbrev=False,
    )
    accept_parser.add_argument(
        "--fixtures",
        type=Path,
        required=True,
        help="Directory containing ProblemSpec fixture files.",
    )
    accept_parser.add_argument(
        "--output-dir",
        dest="output_dir",
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


def _run_file_mode(args: argparse.Namespace) -> None:
    payload = json.loads(args.input.read_text(encoding="utf-8"))
    problem_spec = ProblemSpec.from_dict(payload)
    thinker = CogAThinker(problem_spec.to_session_state(), profile=_load_profile(args))
    artifact, verdict = thinker.respond(problem_spec.user_input)
    _write_outputs(args.output_dir, artifact, verdict)


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args(sys.argv[1:])

    if args.command == "run":
        _run_file_mode(args)
        return
    if args.command == "accept":
        run_acceptance(args.fixtures, args.output_dir)
        return
    raise SystemExit(f"Unknown command: {args.command}")


if __name__ == "__main__":
    main()
