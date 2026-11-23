#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.."

out=${1:-dist}
mkdir -p -- "$out"
out=$(cd -- "$out" && pwd)
work=$(mktemp -d)
trap 'rm -rf -- "$work"' EXIT

revision=$(git rev-parse HEAD)
if [[ -n $(git status --porcelain) ]]; then
    revision+=-dirty
fi
version=$(.venv/bin/python -c 'import tomllib; from pathlib import Path; print(tomllib.loads(Path("pyproject.toml").read_text())["project"]["version"])')
name="core-api-$version-linux-amd64-$revision"
image="papiliovpn/core-api:$version-$revision"
bundle="$work/core-api"

.venv/bin/python -m pip wheel --no-deps --wheel-dir "$out" .
docker build --platform linux/amd64 --file deploy/Dockerfile --tag "$image" .
mkdir -p "$bundle/deploy" "$bundle/scripts/install" "$bundle/scripts/run"
cp install.sh run.sh config.yml.sample README*.md "$bundle/"
cp -r assets "$bundle/"
cp deploy/compose.yml "$bundle/deploy/"
cp scripts/terminal.sh "$bundle/scripts/"
cp scripts/install/runtime.sh "$bundle/scripts/install/"
cp scripts/run/runtime.sh "$bundle/scripts/run/"
printf '%s\n' "$image" > "$bundle/image-name"
docker save --output "$bundle/image.tar" "$image"

archive="$name.tar.gz"
tar -czf "$out/$archive" -C "$work" core-api
(
    cd -- "$out"
    sha256sum "$archive" > "$archive.sha256"
    sha256sum --check "$archive.sha256"
)
if [[ -n ${GITHUB_OUTPUT:-} ]]; then
    printf 'name=%s\n' "$name" >> "$GITHUB_OUTPUT"
fi
