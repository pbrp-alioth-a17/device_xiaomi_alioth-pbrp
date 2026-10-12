#!/bin/bash
# SPDX-License-Identifier: Apache-2.0
# Offline packaging only. Require a caller-supplied matching ROM or Boot image.
set -eo pipefail
PBRP_ROM=${1:-${PBRP_ROM:-}}
PBRP_METADATA_BOOT=${2:-${PBRP_METADATA_BOOT:-}}
PBRP_SECURITY_PATCH=${3:-${PBRP_SECURITY_PATCH:-}}
cd "$(dirname "$(readlink -f -- "${BASH_SOURCE[0]}")")/../../../.."
if [[ -n ${PBRP_ROM:-} && -n ${PBRP_METADATA_BOOT:-} ]]; then
    echo "Set only one of PBRP_ROM or PBRP_METADATA_BOOT" >&2
    exit 2
elif [[ -n ${PBRP_ROM:-} ]]; then
    args=(--rom "$PBRP_ROM")
elif [[ -n ${PBRP_METADATA_BOOT:-} ]]; then
    args=(--metadata-boot "$PBRP_METADATA_BOOT")
else
    echo "Set PBRP_ROM or PBRP_METADATA_BOOT to matching installed-ROM metadata" >&2
    exit 2
fi
[[ -z ${PBRP_SECURITY_PATCH:-} ]] || args+=(--security-patch "$PBRP_SECURITY_PATCH")
python3 device/xiaomi/alioth/tools/package-recovery.py "${args[@]}"
python3 device/xiaomi/alioth/tools/package-installer.py
