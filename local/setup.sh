#!/bin/bash
# One-time setup: installs this repo into <base>/.venv (the repo's parent folder,
# or COSTCO_BASE), with data in <base>/data. Nothing personal lives in the repo.
set -e
REPO="$(cd "$(dirname "$(readlink -f "$0")")/.." && pwd)"
BASE="${COSTCO_BASE:-$(dirname "$REPO")}"
cd "$BASE"
PY=$(command -v python3.13 || command -v python3.12 || command -v python3.11 || command -v python3.10 || command -v python3)
"$PY" -c 'import sys; sys.exit(not (3, 10) <= sys.version_info[:2] < (3, 14))' || { echo "Need Python 3.10-3.13 (try: brew install python@3.13)"; exit 1; }
"$PY" -m venv .venv
PIP_NO_CACHE_DIR=1 .venv/bin/pip install -q -e "$REPO[dev]"
mkdir -p data
ln -sf "$REPO/local/costco" "$BASE/costco"
echo "Done. Next: $BASE/costco login"
