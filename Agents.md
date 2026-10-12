# Alioth Android 17 PBRP development

## Sources and build

- Work in `~/pbrp-alioth-a17`; preserve the separate ROM and Android 14 recovery checkouts.
- Publish custom projects to [pbrp-alioth-a17](https://github.com/pbrp-alioth-a17), using the tracking [manifest](https://github.com/pbrp-alioth-a17/manifest). Preserve imported authorship and separate unrelated changes.
- Platform: Android 17, LineageOS 24; Alioth and Aliothin device identifiers.
- PBRP uses the scoped recovery layer in `vendor/lineage`; do not restore the retired duplicate vendor project or inherit the Lineage ROM common product for recovery. Preserve recovery flags, tools, policy and versioning while using A17 Lineage kernel/header infrastructure.
- Use `pb_alioth-cp2a-user` and checkout-provided compilers/JDK. The kernel wrapper builds the checked-out sm8250 source with Alioth configuration and stages matching Image/DTB/DTBO checksums.
- Build Boot only. Header v3; Boot partition 201326592 bytes. Never flash the generated placeholder vendor_boot.
- Package with matching installed-ROM OS/security-patch metadata. Keep theme equality, recovery policy, ramdisk integrity, ZIP payload and image checks enabled. Signing uses recovery-local tools and the public AOSP test key.

## Preserve the approved implementation

- Preserve PBRP branding in About in both themes. Material uses compact grouped controls and bounded dialogs; Original and external themes retain their resources. Android and SDK labels come from runtime properties.
- UI/touch, manual brightness, RTC correction, AW8697 timed haptics and configured 120 Hz/120 FPS. No claim of measured frame pacing.
- FBE policy v2 and the existing backup archive policy format. Recovery reads existing keys; do not rewrite credentials or upgrade stored key blobs.
- Qualcomm Keymaster/Gatekeeper/keystore2 services and bounded service waits. Keep installed Android System outside the recovery runtime at `/system_root`.
- Virtual A/B update_engine and snapshot lifecycle; no destructive custom payload installer.
- Boot, Vendor Boot, DTBO and Data backup exposure, default Boot only. Keep protected service partitions and unsupported filesystem operations hidden.
- Current/image/ZIP recovery installation replaces only active Boot's ramdisk and preserves its kernel/header. ZIP installation checks written bytes and does not switch slots or reboot automatically.
- Bundled unmodified Magisk v31.0 runs only on explicit action in an isolated mount namespace. No KernelSU integration.
- Only shared recovery is permissive. Infrastructure services enforce; Android policy and neverallow checks remain enabled.

## Verification boundary

The previous Android 14 recovery's device results are historical. This Android 17
port has passed offline build, host ADB, crypto-vector, MTP lifecycle and
packaging checks recorded in README.md; do not report it ready until
its exact packaged image passes the relevant phone checks.

Use Windows `D:/platform-tools` for the connected phone. Copy an image to a
Windows-local path and verify its hash before temporary `fastboot boot`.
Temporary boot does not authorize flashing or formatting. Preserve userdata;
do not perform Data restore merely for verification. Never request or record
unlock credentials in chat. Restore changed device settings and return to Android.

Track source, compile and runtime results separately. Check USB/ADB/MTP,
UI/touch/haptics, decryption, non-destructive Boot backup and supported menus.
Record untested credential types, physical variants and destructive install
operations as limits. Keep publication links tied to the actual final commits.
