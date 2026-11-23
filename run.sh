#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
case "${1:-runtime}" in
    runtime) exec bash scripts/run/runtime.sh "${@:2}" ;;
    test) exec bash scripts/run/test.sh "${@:2}" ;;
    -h|--help)
        printf 'Usage:\n  ./run.sh [runtime [up|stop|logs|status|migrate|seed|owner]]\n  ./run.sh test [pytest arguments...]\n'
        ;;
    *) printf 'Run ./run.sh --help for usage.\n' >&2; exit 2 ;;
esac
