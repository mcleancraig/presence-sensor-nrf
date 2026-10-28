#!/usr/bin/env bash
# Download zephyr.uf2 from the latest successful CI build of the current branch.
# Usage: scripts/fetch-firmware.sh [--debug] [branch]   (output: build/zephyr/zephyr.uf2)
#   --debug  fetch the USB-logging debug build instead of the release build
set -euo pipefail

cd "$(dirname "$0")/.."
ARTIFACT=firmware
if [[ "${1:-}" == "--debug" ]]; then
    ARTIFACT=firmware-debug
    shift
fi
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
