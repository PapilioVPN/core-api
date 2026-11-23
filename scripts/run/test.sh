#!/usr/bin/env bash
set -euo pipefail
source scripts/terminal.sh
[[ -x .venv/bin/pytest ]] || die 'Run ./install.sh test first.'

work=$(mktemp -d)
container=''
cleanup() {
    if [[ -n $container ]]; then
        docker rm -f "$container" >/dev/null 2>&1 || true
    fi
    rm -rf -- "$work"
}
trap cleanup EXIT

step 'Start an isolated test database'
container=$(docker run --rm --detach --publish 127.0.0.1::5432 \
    -e POSTGRES_USER=papiliovpn -e POSTGRES_DB=papiliovpn \
    -e POSTGRES_PASSWORD=isolated-test-only postgres:17-bookworm)
for ((attempt = 0; attempt < 60; attempt++)); do
    if docker exec "$container" pg_isready -h 127.0.0.1 -U papiliovpn -d papiliovpn >/dev/null; then
        break
    fi
    sleep 1
done
if (( attempt == 60 )); then
    docker logs "$container" >&2
    die 'The test database did not become ready.'
fi

address=$(docker port "$container" 5432/tcp)
export PAPILIOVPN_TEST_POSTGRES_DSN="postgresql+asyncpg://papiliovpn:isolated-test-only@$address/papiliovpn"
export PAPILIO_CONFIG="$work/config.yml"
.venv/bin/python - <<'PY'
from os import environ
from pathlib import Path

import yaml

config = yaml.safe_load(Path("config.yml.sample").read_text())
dsn = environ["PAPILIOVPN_TEST_POSTGRES_DSN"]
config["db"].update(dsn=dsn, test_dsn=dsn)
config["jwt"]["secret_key"] = "isolated-test-only-token-signing-key"
config["crypto"]["password_salt"] = "isolated-test-only-password-salt"
Path(environ["PAPILIO_CONFIG"]).write_text(yaml.safe_dump(config))
PY
.venv/bin/alembic upgrade head
.venv/bin/alembic check
.venv/bin/pytest "$@"
