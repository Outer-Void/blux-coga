#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -eq 0 ]; then
  echo "Usage: ./CogA.sh run --in <problem.json> --out <out_dir> [--profile <id>|--profile-file <path>] [--interactive]"
  exit 1
fi

PYTHON_BIN="python3"
if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  PYTHON_BIN="python"
fi

if [ ! -d ".venv" ]; then
  "$PYTHON_BIN" -m venv .venv
fi

# shellcheck disable=SC1091
. .venv/bin/activate

INSTALL_TARGET="."
if python - <<'PY'
from pathlib import Path
import tomllib
data = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
extras = data.get("project", {}).get("optional-dependencies", {})
raise SystemExit(0 if "dev" in extras else 1)
PY
then
  INSTALL_TARGET=".[dev]"
fi

python -m pip install -e "$INSTALL_TARGET"
ARGS=("$@")
if [ "${#ARGS[@]}" -gt 0 ] && [ "${ARGS[0]}" != "run" ] && [ "${ARGS[0]}" != "accept" ] && [ "${ARGS[0]}" != "-h" ] && [ "${ARGS[0]}" != "--help" ]; then
  ARGS=(run "${ARGS[@]}")
fi
python -m blux_coga "${ARGS[@]}"
