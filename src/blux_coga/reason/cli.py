"""`coga` command line (docs/USAGE.md). The frozen CogA 1.0 contract stays at `blux-coga run`."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from blux_coga import __version__
from blux_coga.reason import blux_adapter
from blux_coga.reason.common import ALGORITHMS, ENGINE_VERSION, CogaError, parse_request, schema
from blux_coga.reason.engine import replay, run
from blux_coga.reason.evaluate import run_suite

EXIT_OK, EXIT_CHECK_FAILED, EXIT_USAGE, EXIT_FAILURE = 0, 1, 2, 3
SHORT = {cap.split(".", 1)[1]: cap for cap in ALGORITHMS}
DEFAULT_SUITE = Path(__file__).resolve().parent / "evals"


def _read(path: str) -> Any:
    try:
        data = sys.stdin.buffer.read() if path == "-" else Path(path).read_bytes()
    except OSError as exc:
        raise CogaError("UNREADABLE", f"Cannot read {path}: {exc.strerror}.") from None
    return parse_request(data)


def _emit(doc: Any, args: argparse.Namespace) -> None:
    text = json.dumps(
        doc,
        sort_keys=True,
        indent=2 if args.pretty else None,
        ensure_ascii=False,
        separators=None if args.pretty else (",", ":"),
    )
    if getattr(args, "out", None):
        Path(args.out).write_text(text + "\n", encoding="utf-8")
    else:
        sys.stdout.write(text + "\n")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="coga",
        description="CogA 2: deterministic, explicit reasoning structures (no model, no hidden chain-of-thought).",
        epilog="Exit codes: 0 ok, 1 replay mismatch or failed evaluation, 2 usage, 3 invalid request or failure.",
    )
    p.add_argument("--version", action="version", version=f"coga {ENGINE_VERSION} (blux-coga {__version__})")
    sub = p.add_subparsers(dest="command", metavar="COMMAND")
    for short, cap in sorted(SHORT.items()):
        s = sub.add_parser(short, help=f"{cap}: request JSON (or -) in, coga.artifact out")
        s.add_argument("request")
        s.add_argument("-o", "--out")
        s.add_argument("--pretty", action="store_true")
    s = sub.add_parser("replay", help="recompute an artifact and check it reproduces exactly")
    s.add_argument("artifact")
    s.add_argument("--request", required=True)
    s.add_argument("-o", "--out", help="write the recomputed artifact (for blux-system replay-check --output)")
    s.add_argument("--pretty", action="store_true")
    s = sub.add_parser("validate", help="check a request against a capability's schema and references")
    s.add_argument("capability", choices=sorted(SHORT))
    s.add_argument("request")
    s = sub.add_parser("schema", help="print a JSON Schema")
    s.add_argument("capability", choices=sorted(SHORT))
    s.add_argument("--artifact", action="store_true", help="the output schema instead of the request schema")
    s = sub.add_parser("eval", help="run a regression/adversarial suite (default: the bundled evals/)")
    s.add_argument("suite", nargs="?", type=Path)
    s.add_argument("--pretty", action="store_true")
    sub.add_parser("capabilities", help="list capabilities and algorithm versions")
    s = sub.add_parser("blux-capability")  # BLUX ADR-0009 entrypoint
    s.add_argument("capability_id", choices=sorted(ALGORITHMS))
    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return EXIT_OK if exc.code == 0 else EXIT_USAGE
    if args.command is None:
        parser.print_help()
        return EXIT_USAGE
    if args.command == "blux-capability":
        return blux_adapter.main(args.capability_id)
    try:
        if args.command in SHORT:
            _emit(run(SHORT[args.command], _read(args.request)), args)
        elif args.command == "replay":
            report = replay(_read(args.artifact), _read(args.request))
            if args.out:
                Path(args.out).write_text(json.dumps(report["artifact"], sort_keys=True) + "\n", encoding="utf-8")
            args.out = None
            _emit({k: v for k, v in report.items() if k != "artifact"}, args)
            return EXIT_OK if report["ok"] else EXIT_CHECK_FAILED
        elif args.command == "validate":
            run(SHORT[args.capability], _read(args.request))
            print(f"valid {SHORT[args.capability]} request")
        elif args.command == "schema":
            kind = "artifact" if args.artifact else "request"
            print(json.dumps(schema(f"{SHORT[args.capability]}.{kind}.v1.json"), indent=2, sort_keys=True))
        elif args.command == "eval":
            report = run_suite(args.suite or DEFAULT_SUITE)
            args.out = None
            _emit(report, args)
            return EXIT_OK if report["verdict"] == "pass" else EXIT_CHECK_FAILED
        else:
            for cap, algo in sorted(ALGORITHMS.items()):
                print(f"{cap:<18} {cap}/{algo}")
    except CogaError as exc:
        print(json.dumps({"error": exc.to_dict()}, sort_keys=True), file=sys.stdout)
        print(f"coga: {exc.code}: {exc.message}", file=sys.stderr)
        return EXIT_FAILURE
    return EXIT_OK
