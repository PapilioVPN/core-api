#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
case "${1:-runtime}" in
    runtime) exec bash scripts/install/runtime.sh "${@:2}" ;;
    test) exec bash scripts/install/test.sh ;;
    -h|--help) printf 'Usage: ./install.sh [runtime [IMAGE@sha256:DIGEST] | test]\n' ;;
    *) printf 'Run ./install.sh --help for usage.\n' >&2; exit 2 ;;
esac
