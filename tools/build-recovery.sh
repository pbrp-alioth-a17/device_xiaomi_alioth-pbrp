#!/usr/bin/env bash
set -eo pipefail
cd "$(dirname -- "${BASH_SOURCE[0]}")/../../../.."
source build/envsetup.sh
lunch pb_alioth-cp2a-user
m -j"${JOBS:-8}" bootimage
