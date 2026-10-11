#!/usr/bin/env bash
set -eo pipefail
cd "$(dirname -- "${BASH_SOURCE[0]}")/../../../.."
pbrp_root="$PWD"
pbrp_kernel="$pbrp_root/kernel/xiaomi/sm8250"
pbrp_kernel_out="$pbrp_root/out/kernel-alioth"
export PATH="$pbrp_root/prebuilts/clang/host/linux-x86/clang-r563880c/bin:$pbrp_root/prebuilts/kernel-build-tools/linux-x86/bin:$PATH"
pbrp_make_args=( -C "$pbrp_kernel" O="$pbrp_kernel_out" ARCH=arm64 LLVM=1 LLVM_IAS=1 CROSS_COMPILE=aarch64-linux-gnu- CROSS_COMPILE_COMPAT=arm-linux-gnueabi- )
make "${pbrp_make_args[@]}" alioth_defconfig
make "${pbrp_make_args[@]}" -j"${JOBS:-4}" Image dtbs dtbo.img
mkdtimg dump "$pbrp_kernel_out/arch/arm64/boot/dtbo.img" >/dev/null
python3 - "$pbrp_root" <<'PY'
from pathlib import Path
import hashlib, shutil, sys
root = Path(sys.argv[1]).resolve()
boot = root / "out/kernel-alioth/arch/arm64/boot"
prebuilt = root / "device/xiaomi/alioth/prebuilt"
image = (boot / "Image").read_bytes()
if image[56:60] != b"ARMd":
    raise SystemExit("Invalid ARM64 kernel image")
dtbs = []
for name in ("kona.dtb", "kona-v2.dtb", "kona-v2.1.dtb"):
    data = (boot / "dts/vendor/qcom" / name).read_bytes()
    if data[:4] != bytes.fromhex("d00dfeed"):
        raise SystemExit("Invalid device tree: " + name)
    dtbs.append(data)
shutil.copy2(boot / "Image", prebuilt / "Image")
shutil.copy2(boot / "dtbo.img", prebuilt / "dtbo.img")
(prebuilt / "dtbs/alioth.dtb").write_bytes(b"".join(dtbs))
files = ("Image", "dtbs/alioth.dtb", "dtbo.img")
(prebuilt / "SHA256SUMS").write_text("".join(
    hashlib.sha256((prebuilt / name).read_bytes()).hexdigest() + "  " + name + "\n"
    for name in files))
PY
