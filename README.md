# PitchBlack Recovery — POCO F3 / Redmi K40 / Mi 11X

PBRP 4.0 port to Android 17 recovery userspace (LineageOS 24 platform base).
The port is under build and runtime validation. Supported codenames: **alioth, aliothin**.

Source and future releases: [pbrp-alioth-a17/device_xiaomi_alioth-pbrp](https://github.com/pbrp-alioth-a17/device_xiaomi_alioth-pbrp). No release assets have been published in this standalone repository.

## Installation

- Temporary launch: `fastboot boot recovery_boot.img`.
- Permanent installation: Advanced → **Install Current Recovery**,
  or **Install Recovery from Image**. The current option appears first.
- `recovery.zip` installs the recovery ramdisk into **active Boot**, retaining
  its kernel/header. It requires neither decrypted storage nor a persistent
  backup. Signed ZIP installation and written-image verification passed on October 9.
- Reinstall Magisk after ramdisk installation. Magisk v31.0 is bundled under
  Tools, with official provenance and checksum alongside the package.

Do not flash the generated placeholder vendor_boot. Neither image nor ZIP
formats userdata. Only the shared recovery domain remains permissive; infrastructure services enforce.
Android policy and neverallow checks remain intact. It is not fully enforcing.

## Historical verification and remaining checks

The previous Android 14 recovery implementation verified: UI/touch, brightness, timed haptics, RTC, 120 Hz selection, MTP,
Boot backup, Android 17 password decryption, Virtual A/B ROM sideload,
Magisk installation and current-recovery ramdisk installation.
Data restore, other credential types and physical Mi 11X/Redmi K40 testing
remain unverified. Final fastboot USB driver compatibility is pending. GUI frame pacing is configured for 120 FPS.

## Rebuild

Use the Android 17 checkout at `~/pbrp-alioth-a17` with this tree at
`device/xiaomi/alioth`. Android 14 build trees are not supported by this port.
Use the [Android 17 source manifest](https://github.com/pbrp-alioth-a17/manifest). Its pinned projects contain the required changes; do not replay the old Android 14 patch series. See the [source guide](patches/README.md).
The matching Android 17 kernel/DTB/DTBO are tracked in `prebuilt/`:
`Image`, `dtbs/`, and `dtbo.img`. The build wrapper regenerates them from
`kernel/xiaomi/sm8250` using the checkout-provided compiler before building recovery.
Run `device/xiaomi/alioth/tools/build-recovery.sh` (user build, Boot only).

Package against the matching installed ROM ZIP to keep Keymaster OS/security
patch metadata correct:

```sh
python3 device/xiaomi/alioth/tools/package-recovery.py --rom /path/to/ROM.zip
python3 device/xiaomi/alioth/tools/package-installer.py
```

Deliverables: `out/release-candidate/recovery_boot.img`, `recovery.zip` and
`SHA256SUMS`. ZIP signing uses the public AOSP test key, not a private release key.
Development handoff: [Agents.md](Agents.md).

## Recovery runtime and current ROM metadata

The recovery runtime keeps the installed Android System outside recovery's
/system and isolate bundled Magisk mounts. The Boot OS/security-patch header must
match the installed ROM, or Keymaster can reject metadata-encryption keys.
For incremental work without the ROM ZIP, retain OS metadata from a previously
matched Boot image and explicitly supply a verified current patch if it changed:

```sh
python3 device/xiaomi/alioth/tools/package-recovery.py \
  --metadata-boot /path/to/previous-recovery.img --security-patch 2026-10
```

October 2026 is the observed current ROM patch, not a permanent default for all
future releases. This does not authorize access to ~/evo/out.

### Recovery-local installer signing

After `lunch pb_alioth-cp2a-user`, run `m -j4 signapk` in the recovery checkout
before `python3 device/xiaomi/alioth/tools/package-installer.py`. Signing uses
recovery-local JDK 21, SignApk, JNI libraries and AOSP public test keys. The
packager fails before creating the ZIP if signing tools are missing. It never
uses the ROM output directory. CRC, embedded image equality and both payload
checksums are checked explicitly, including under optimized Python.

## Android 17 offline feature audit

The current candidate is not a production release. Its exact image still needs
phone verification; the Android 14 results above do not validate this port.

| Area | Current source/build evidence | Remaining runtime check |
| --- | --- | --- |
| Navigation and tools | All 50 bundled theme action names resolve to registered handlers | Touch every supported menu; check labels and spacing |
| Appearance | Original PBRP remains the default; Customizations offers Android 17 Material colors. The selection is saved and reloaded after settings load; external palettes retain their colors | Inspect both palettes, reboot persistence and contrast on bitmap controls |
| Flashlight | Torch discovery requires a matching brightness node; directory handles close. Failed writes report errors and activation rolls back | Check Alioth torch on/off and intensity |
| Brightness and hardware writes | Shared helpers check short writes and close/flush failures; disposable host ENOSPC checks passed | Verify panel brightness and haptic controls |
| FBE and metadata encryption | Generated kernel enables filesystem encryption and inline crypto; native Android 17 fscrypt paths and staged crypto dependencies compile | Existing credential decryption and storage access, without rewriting keys |
| Virtual A/B | Generated kernel enables dm-user and dm-snapshot; native snapshot libraries and updater dependencies are packaged | Sideload and snapshot lifecycle against a compatible OTA |
| USB | Generated kernel enables USB configfs/FunctionFS; staged init scripts and executable dependencies pass packaging checks | ADB authorization, MTP and fastbootd |
| Backup and recovery installation | Approved partition exposure and active-Boot-only ramdisk installation remain intact | Non-destructive Boot backup; destructive operations remain unverified |
| SELinux | Android 17 policy compilation and neverallow/type tests pass; only the shared recovery domain is permissive | Audit denials from the exact booted candidate |

The additional appearance option follows Material color roles, not Android's
framework UI toolkit: PBRP still uses its native XML/bitmap interface. It does not
claim Android Settings components, dynamic wallpaper colors or blur support.
Reference: [Material color roles](https://m3.material.io/styles/color/roles),
[AOSP FBE](https://source.android.com/docs/security/features/encryption/file-based),
[AOSP Virtual A/B](https://source.android.com/docs/core/ota/virtual_ab).

The packaging review additionally rejects ramdisk symlink traversal into the
build host, checks the full generated theme XML for stale content, and enforces
the configured Boot partition size before publishing a candidate. Disposable
host fixtures cover symlink escapes/loops and stale theme rejection; no test
harnesses are installed in recovery or added to its source history.
## Final offline candidate — 2026-10-11

The user-build recovery and Android 17 policy targets build successfully.
The existing ADB host suite passes 124 tests; one vsock test is excluded and
one is skipped because the WSL host lacks that transport. Six extracted ADB
authorization-gate cases preserve authentication on locked user builds.
Both recovery scrypt reference and SSE implementations match three independent
known vectors each; this does not exercise ARM NEON or Qualcomm hardware keys.

MTP uses FunctionFS descriptors and waits for MTP readiness, and for ADB
readiness when combined. Host checks cover all 16 readiness combinations and
real-child shutdown/reaping without consuming unrelated children. All 20
packaged init scripts pass Android 17 host_init_verifier. Both original and
Material palette loading, saved-selection reload and external-palette isolation
pass source-based host checks. Packaging validates ELF dependencies, generated
theme freshness, ramdisk paths, policy boundaries and installer payloads.
No temporary test harnesses are committed or installed.

Artifacts in `out/release-candidate/`:

- Boot image: 117092352 bytes; SHA-256 `aaef9f77fab5685bfe9a36086e4971babffbce2c7b767e2ac79026de51e599cb`.
- Installer ZIP: 87025090 bytes; SHA-256 `a2b0d5967331d8b9874f68ddbbc789bd4d2d9efed715f5c5e3f56ea3e36e7baa`.

Physical ADB authorization/USB, MTP transfers, existing-data decryption and
visual inspection of both palettes remain pending on this exact image.
These offline checks do not certify a production release or full enforcing
operation: the shared recovery domain remains permissive.
