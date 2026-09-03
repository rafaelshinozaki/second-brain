#!/usr/bin/env bash
# Runs the smoke test. Creates a local venv with the MCP SDK on first run.
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV="$DIR/.venv"

if [ ! -d "$VENV" ]; then
  echo "Creating virtualenv with the MCP SDK..."
  python3 -m venv "$VENV"
  # shellcheck disable=SC1091
  source "$VENV/bin/activate"
  pip -q install --upgrade pip >/dev/null
  pip -q install "mcp>=1.2"
else
  # shellcheck disable=SC1091
  source "$VENV/bin/activate"
fi

python "$DIR/scripts/test-brain.py" "$@"
