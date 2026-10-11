# Alioth recovery kernel prebuilts

Source: [PocoF3Releases/kernel_xiaomi_sm8250](https://github.com/PocoF3Releases/kernel_xiaomi_sm8250/commit/a67e83add1fa9398814db8451f91347c7c2d09ed), branch `aosp-17`.

Built in the Android 17 recovery checkout with `alioth_defconfig`, Clang
r563880c and LLVM tools. Includes the current ROM kernel fixes. The DTB image
concatenates kona.dtb, kona-v2.dtb and kona-v2.1.dtb; DTBO contains only the
Alioth overlay selected by the kernel configuration.

BoardConfig uses Image, dtbs/alioth.dtb and dtbo.img. SHA256SUMS records the
exact staged bytes. No KernelSU integration. Compilation and DTBO structure
checks passed; on-device acceptance of this refresh is still pending.
