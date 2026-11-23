#!/usr/bin/env bash
set -euo pipefail
source scripts/terminal.sh

export CORE_STATE=${CORE_STATE:-$PWD/.local/runtime}
[[ -s $CORE_STATE/image-name ]] || die 'Run ./install.sh runtime first.'
CORE_STATE=$(cd -- "$CORE_STATE" && pwd)
read -r CORE_IMAGE < "$CORE_STATE/image-name"
export CORE_IMAGE
compose=(docker compose --project-name "${CORE_PROJECT:-papiliovpn-core}" --file deploy/compose.yml)
profile=()
if [[ ${CORE_JOBS:-0} == 1 ]]; then
    profile=(--profile jobs)
fi

case "${1:-up}" in
    up)
        step 'Start PostgreSQL and Redis'
        "${compose[@]}" up --detach --wait --wait-timeout 120 postgres redis
        step 'Apply database migrations'
        "${compose[@]}" run --rm --no-deps api alembic upgrade head
        step 'Start Core API'
        "${compose[@]}" "${profile[@]}" up --detach --wait --wait-timeout 120
        success "API available on http://${CORE_BIND:-127.0.0.1}:${CORE_PORT:-8000}"
        ;;
    stop) "${compose[@]}" --profile jobs down ;;
    logs) "${compose[@]}" --profile jobs logs --follow --tail 100 ;;
    status) "${compose[@]}" --profile jobs ps --all ;;
    migrate) "${compose[@]}" run --rm api alembic upgrade head ;;
    owner)
        tty=()
        if [[ ! -t 0 ]]; then
            tty=(-T)
        fi
        "${compose[@]}" run --rm "${tty[@]}" api papiliovpn-core users owner
        ;;
    *) die 'Choose up, stop, logs, status, migrate or owner.' ;;
esac
