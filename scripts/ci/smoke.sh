#!/usr/bin/env bash
set -euo pipefail
archive=$(realpath -- "${1:?Provide the packaged runtime archive.}")
work=$(mktemp -d)
export CORE_PROJECT="core-smoke-${work##*.}"
CORE_PROJECT=${CORE_PROJECT,,}
export CORE_STATE="$work/state" CORE_BIND=127.0.0.1 CORE_PORT=0 CORE_JOBS=1
compose=(docker compose --project-name "$CORE_PROJECT" --file "$work/core-api/deploy/compose.yml" --profile jobs)

cleanup() {
    if [[ -s $CORE_STATE/image-name ]]; then
        export CORE_IMAGE
        read -r CORE_IMAGE < "$CORE_STATE/image-name"
        "${compose[@]}" down --volumes >/dev/null 2>&1 || true
    fi
    rm -rf -- "$work"
}
trap cleanup EXIT
trap 'if [[ -s $CORE_STATE/image-name ]]; then "${compose[@]}" logs --tail 80 >&2 || true; fi' ERR

(
    cd -- "$(dirname -- "$archive")"
    sha256sum --check "$(basename -- "$archive").sha256"
)
tar -xzf "$archive" -C "$work"
cd -- "$work/core-api"
./install.sh runtime
export CORE_IMAGE
read -r CORE_IMAGE < "$CORE_STATE/image-name"
state=$(sha256sum "$CORE_STATE/config.yml" "$CORE_STATE/db.password")
./install.sh runtime
[[ $(sha256sum "$CORE_STATE/config.yml" "$CORE_STATE/db.password") == "$state" ]]

CORE_JOBS=0 ./run.sh runtime up
address=$("${compose[@]}" port api 8000)
curl --fail --silent --show-error "http://$address/health"
printf '\n'
owner() {
    printf '%s\n' Owner Smoke 09120000001 isolated-owner-test isolated-owner-test |
        ./run.sh runtime owner
}
owner
if owner; then
    printf 'Owner setup unexpectedly succeeded a second time.\n' >&2
    exit 1
fi

python3 - "$address" <<'PY'
import json
import sys
from urllib.request import Request, urlopen

base = "http://" + sys.argv[1]
request = Request(
    base + "/admin/auth/tokens",
    data=json.dumps({
        "mobile": "09120000001",
        "password": "isolated-owner-test",
    }).encode(),
    headers={"Content-Type": "application/json"},
)
with urlopen(request, timeout=5) as response:
    token = json.load(response)["data"]["access_token"]

request = Request(
    base + "/admin/account/me",
    headers={"Authorization": "Bearer " + token},
)
with urlopen(request, timeout=5) as response:
    assert json.load(response)["data"]["is_super_admin"] is True
PY

./run.sh runtime up
running=$("${compose[@]}" ps --status running --services)
for service in api postgres redis nats scheduler beat events; do
    grep -Fxq "$service" <<< "$running"
done
./run.sh runtime migrate
printf 'Runtime archive verified.\n'
