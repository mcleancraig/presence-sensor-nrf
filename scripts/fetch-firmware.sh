#!/usr/bin/env bash
# Download zephyr.uf2 from the latest successful CI build of the current branch.
# Usage: scripts/fetch-firmware.sh [--ld2410c] [--debug] [branch]   (output: build/zephyr/zephyr.uf2)
#   --ld2410c  fetch the HLK-LD2410C radar variant instead of the default HLK-LD2410S build
#   --debug    fetch the USB-logging debug build instead of the release build
set -euo pipefail

cd "$(dirname "$0")/.."
MODEL=""
DEBUG=""
while [[ "${1:-}" == --* ]]; do
    case "$1" in
        --ld2410c) MODEL="-ld2410c"; shift ;;
        --debug)   DEBUG="-debug"; shift ;;
        *) echo "Unknown flag: $1 (expected --ld2410c and/or --debug)" >&2; exit 1 ;;
    esac
done
ARTIFACT="firmware${MODEL}${DEBUG}"
BRANCH="${1:-$(git rev-parse --abbrev-ref HEAD)}"

RUN_ID=$(gh run list --workflow build.yml --branch "$BRANCH" --status success \
    --limit 1 --json databaseId --jq '.[0].databaseId')
if [[ -z "$RUN_ID" ]]; then
    echo "No successful build found for branch '$BRANCH'" >&2
    exit 1
fi

rm -rf build/zephyr
mkdir -p build/zephyr
gh run download "$RUN_ID" --name "$ARTIFACT" --dir build/zephyr

echo "$ARTIFACT from run $RUN_ID ($(gh run view "$RUN_ID" --json headSha --jq '.headSha[0:7]')):"
ls -l build/zephyr/zephyr.uf2
