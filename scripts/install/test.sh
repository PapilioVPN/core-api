#!/usr/bin/env bash
set -euo pipefail
source scripts/terminal.sh

step 'Prepare Python 3.13 and test dependencies'
[[ -x .venv/bin/python ]] || python3.13 -m venv .venv
.venv/bin/python -m pip install -e '.[dev,tasks]'
.venv/bin/python -m pip check
success 'Tests are ready. Run ./run.sh test.'
