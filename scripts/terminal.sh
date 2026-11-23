#!/usr/bin/env bash

accent='' good='' bad='' reset=''
if [[ -t 1 && -z ${NO_COLOR:-} && ${TERM:-dumb} != dumb ]]; then
    accent=$'\033[1;36m' good=$'\033[1;32m'
    bad=$'\033[1;31m' reset=$'\033[0m'
fi
step() { printf '%s→%s %s\n' "$accent" "$reset" "$1"; }
success() { printf '%s✓%s %s\n' "$good" "$reset" "$1"; }
die() { printf '%s✗%s %s\n' "$bad" "$reset" "$1" >&2; exit 1; }
