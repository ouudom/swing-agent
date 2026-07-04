#!/usr/bin/env bash
# Cross-environment Python launcher for the trading pipeline.
#
# Why this exists: the macOS .venv is a broken symlink inside the Linux scheduled-task
# sandbox, so hardcoding .venv/bin/python breaks unattended /validate and /weekly runs.
#
#   - macOS (local interactive): uses the project's .venv if its interpreter works.
#   - Linux sandbox (scheduled runs): falls back to system python3 + .pydeps,
#     a persistent target-dir install of the deps missing from the base image (yfinance, ...).
#
# Usage:  bash src/engine/scripts/pyrun.sh src/engine/scripts/pipeline/weekly_pull.py --instrument xauusd
#
# Layout note: this launcher lives at swing-agent/src/engine/scripts/pyrun.sh, so ROOT is
# resolved three levels up (scripts -> engine -> src -> swing-agent). requirements.txt lives
# under src/. In Docker the pipeline bypasses this launcher entirely (commands.pyrun detects
# /.dockerenv and calls the interpreter directly) — this path is the LOCAL fallback only.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
REQ="$ROOT/src/requirements.txt"

# 1) Prefer the local venv when its interpreter exists AND has the deps.
#    A broken symlink fails `-x`, so this is skipped automatically in the Linux sandbox.
VENV_PY="$ROOT/.venv/bin/python"
if [ -x "$VENV_PY" ] && "$VENV_PY" -c 'import yfinance' >/dev/null 2>&1; then
  exec "$VENV_PY" "$@"
fi

# 2) Fallback: system python3 + persistent .pydeps (rebuild with: pyrun.sh --setup)
if [ "${1:-}" = "--setup" ]; then
  echo "[pyrun] installing pipeline deps into $ROOT/.pydeps (from $REQ) ..."
  python3 -m pip install --target="$ROOT/.pydeps" -r "$REQ"
  echo "[pyrun] done."
  exit 0
fi
export PYTHONPATH="$ROOT/.pydeps${PYTHONPATH:+:$PYTHONPATH}"
exec python3 "$@"
