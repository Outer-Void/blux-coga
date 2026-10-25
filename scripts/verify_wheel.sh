#!/usr/bin/env bash
# Build the wheel, install it into a clean venv outside the source tree, and use it there: schemas and the
# bundled evaluation suite must ship inside the wheel.
set -euo pipefail
PYTHON="${PYTHON:-python3}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

"$PYTHON" -m build --wheel --outdir "$WORK/dist" "$ROOT" >/dev/null
"$PYTHON" -m venv "$WORK/venv"
"$WORK/venv/bin/pip" install -q "$WORK"/dist/*.whl
cd "$WORK"
"$WORK/venv/bin/coga" --version
"$WORK/venv/bin/coga" eval >"$WORK/eval.json"
"$WORK/venv/bin/python" -c "import json,sys; r=json.load(open(sys.argv[1])); assert r['verdict']=='pass', r" "$WORK/eval.json"
"$WORK/venv/bin/coga" compare "$ROOT/src/blux_coga/reason/evals/cases/compare-basic.json" -o "$WORK/a.json"
"$WORK/venv/bin/coga" replay "$WORK/a.json" --request "$ROOT/src/blux_coga/reason/evals/cases/compare-basic.json" >/dev/null
set +e; echo '{}' | "$WORK/venv/bin/coga" plan - >/dev/null 2>&1; code=$?; set -e
[ "$code" -eq 3 ] || { echo "expected exit 3 for an invalid request, got $code" >&2; exit 1; }
"$WORK/venv/bin/blux-coga" --help >/dev/null  # the frozen 1.0 entry point still installs
echo "verify_wheel: OK"
