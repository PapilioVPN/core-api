#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.."

.venv/bin/ruff check src tests deploy migrations
.venv/bin/ruff format --check src tests deploy migrations
.venv/bin/pyright
while IFS= read -r script; do
    bash -n "$script"
done < <(find scripts -name '*.sh')
bash -n install.sh
bash -n run.sh
./run.sh test "$@"
