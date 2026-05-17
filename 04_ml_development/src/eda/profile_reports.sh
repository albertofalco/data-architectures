#!/bin/bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
PROJECT_ROOT="$(cd -- "$SCRIPT_DIR/../../.." && pwd -P)"

IMAGE_NAME="data-architectures-profile-reports:py313"

docker run --rm \
    --user "$(id -u):$(id -g)" \
    -v "$PROJECT_ROOT":/work \
    -v /tmp:/tmp \
    -w /work \
    "$IMAGE_NAME" \
    python 04_ml_development/src/eda/profile_reports.py "$@"
