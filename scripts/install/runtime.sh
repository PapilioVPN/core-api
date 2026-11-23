#!/usr/bin/env bash
set -euo pipefail
source scripts/terminal.sh
docker compose version >/dev/null

export CORE_STATE=${CORE_STATE:-$PWD/.local/runtime}
[[ -d $CORE_STATE ]] || install -d -m 700 -- "$CORE_STATE"
CORE_STATE=$(cd -- "$CORE_STATE" && pwd)
[[ -O $CORE_STATE && $(stat -c %a -- "$CORE_STATE") == 700 ]] ||
    die 'The state directory must be owned by the operator with mode 0700.'

image=${1:-}
if [[ -n $image ]]; then
    [[ $image =~ @sha256:[a-f0-9]{64}$ ]] || die 'Provide an image by SHA-256 digest.'
    step 'Pull the release image'
    docker pull "$image"
elif [[ -f image.tar && -f image-name ]]; then
    step 'Load the bundled image'
    read -r image < image-name
    docker load --input image.tar
else
    step 'Build the local API image'
    image="papiliovpn/core-api:local$(git rev-parse --short HEAD 2>/dev/null || true)"
    docker build --file deploy/Dockerfile --tag "$image" .
fi

step 'Prepare private settings'
docker run --rm --network none --user "$(id -u):$(id -g)" \
    --mount "type=bind,source=$CORE_STATE,target=/setup" \
    --entrypoint python "$image" /app/configure.py /setup
export CORE_IMAGE=$image
services=(postgres redis)
if [[ ${CORE_JOBS:-0} == 1 ]]; then
    services+=(nats)
fi
step 'Prepare service images'
docker compose --file deploy/compose.yml pull --policy missing "${services[@]}"
printf '%s\n' "$image" > "$CORE_STATE/image-name"
success 'Installed. Run ./run.sh runtime up.'
