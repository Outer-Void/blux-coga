"""CLI harness for CogA."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from blux_coga.contracts.determinism import stable_json_dumps
from blux_coga.contracts.models import ProblemSpec
from blux_coga.core.thinker import CogAThinker
from blux_coga.io.acceptance import run_acceptance


def main() -> None:
    if len(sys.argv) > 1 and sys.argv[1] == "accept":
        accept_parser = argparse.ArgumentParser(
            description="Run CogA acceptance fixtures."
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
        args = accept_parser.parse_args(sys.argv[2:])
        run_acceptance(args.fixtures, args.out)
        return

    parser = argparse.ArgumentParser(description="Run CogA contract processing.")
    parser.add_argument(
        "--input",
        "-i",
        type=Path,
        help="Path to a ProblemSpec JSON file.",
    )
    parser.add_argument(
        "--output-dir",
        "-o",
        type=Path,
        default=Path("out"),
        help="Directory for contract outputs.",
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Run interactive REPL mode.",
    )
    args = parser.parse_args()

    output_dir: Path = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.interactive:
        thinker = CogAThinker()
        while True:
            try:
                user_input = input("> ")
            except EOFError:
                break
            artifact, verdict = thinker.respond(user_input)
            (output_dir / "thought_artifact.json").write_text(
                stable_json_dumps(artifact.to_dict()), encoding="utf-8"
            )
            (output_dir / "reasoning_verdict.json").write_text(
                stable_json_dumps(verdict.to_dict()), encoding="utf-8"
            )
            print(artifact.response_text)
            if thinker.state.stopped or thinker.state.frozen:
                break
        return

    if not args.input:
        raise SystemExit("Provide --input for file mode or use --interactive.")

    payload = json.loads(args.input.read_text(encoding="utf-8"))
    problem_spec = ProblemSpec.from_dict(payload)
    thinker = CogAThinker(problem_spec.to_session_state())
    artifact, verdict = thinker.respond(problem_spec.user_input)
    (output_dir / "thought_artifact.json").write_text(
        stable_json_dumps(artifact.to_dict()), encoding="utf-8"
    )
    (output_dir / "reasoning_verdict.json").write_text(
        stable_json_dumps(verdict.to_dict()), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
