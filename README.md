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
Use the [Android 17 source manifest](https://github.com/pbrp-alioth-a17/manifest). Its tracked project branches contain the required changes; do not replay the old Android 14 patch series. See the [source guide](patches/README.md).
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

The current candidate is not a production release. The exact image passed the
ADB, keystore startup and existing-data MTP checks below; destructive operations
and the remaining feature checks are not certified by those results.

| Area | Current source/build evidence | Remaining runtime check |
| --- | --- | --- |
| Navigation and tools | All 50 bundled theme action names resolve to registered handlers | Touch every supported menu; check labels and spacing |
| Appearance | Original PBRP remains the default; Customizations offers Android 17 Material colors. The selection is saved and reloaded after settings load; external palettes retain their colors | Inspect both palettes, reboot persistence and contrast on bitmap controls |
| Flashlight | Torch discovery requires a matching brightness node; directory handles close. Failed writes report errors and activation rolls back | Check Alioth torch on/off and intensity |
| Brightness and hardware writes | Shared helpers check short writes and close/flush failures; disposable host ENOSPC checks passed | Verify panel brightness and haptic controls |
| FBE and metadata encryption | Generated kernel enables filesystem encryption and inline crypto; native Android 17 fscrypt paths and staged crypto dependencies compile | Existing credential decryption and storage access, without rewriting keys |
| Virtual A/B | Generated kernel enables dm-user and dm-snapshot; native snapshot libraries, the on-demand snapuserd daemon and updater dependencies are packaged | Sideload and snapshot lifecycle against a compatible OTA |
| File manager | Upstream PBRP Info-ZIP is packaged with ZIP64 and UTF-8 support; recursive host archive round-trips preserve names and contents | Create and extract an archive on device storage |
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
## Final candidate — 2026-10-12

The user-build recovery and Android 17 policy targets build successfully.
The existing ADB host suite passes 124 tests; one vsock test is excluded and
one is skipped because the WSL host lacks that transport. Six extracted ADB
authorization-gate cases preserve authentication on locked user builds.
Both recovery scrypt reference and SSE implementations match three independent
known vectors each; this does not exercise ARM NEON or Qualcomm hardware keys.

MTP uses FunctionFS descriptors and waits for MTP readiness, and for ADB
readiness when combined. Host checks cover all 16 readiness combinations and
real-child shutdown/reaping without consuming unrelated children. All 21
packaged init scripts pass Android 17 host_init_verifier. Both original and
Material palette loading, saved-selection reload and external-palette isolation
pass source-based host checks. Packaging validates ELF dependencies, generated
theme freshness, ramdisk paths, policy boundaries and installer payloads.
No temporary test harnesses are committed or installed.

Artifacts in `out/release-candidate/`:

- Boot image: 117993472 bytes; SHA-256 `56fbff2a1736c2a0e8dcde0d1c1d3ef23358fc8c5ee331707bce390bcfdc5f20`.
- Installer ZIP: 87931918 bytes; SHA-256 `373180863fd246b611bf00ba98fbc08381ca85a91ab162f32e836c00cc2964a4`.

Physical ADB authorization/USB, default-credential decryption and readable MTP
folder names pass on this exact image. MTP transfer round-trips, other credential
types and visual inspection of both palettes remain pending.
These offline checks do not certify a production release or full enforcing
operation: the shared recovery domain remains permissive.
## ROM device-tree backend alignment

The recovery audit uses ROM Alioth commit
[c1debf6](https://github.com/PocoF3Releases/device_xiaomi_alioth/commit/c1debf6b85f71d640fa18beea6e9b3e13c79c8c2)
and sm8250-common commit
[38b93bc](https://github.com/PocoF3Releases/device_xiaomi_sm8250-common/commit/38b93bc3b49c3a56302eac6bfcc7c3b12730ee30).
The recovery kernel already matches the ROM kernel at
[a67e83add1fa](https://github.com/pbrp-alioth-a17/kernel_xiaomi_sm8250/commit/a67e83add1fa9398814db8451f91347c7c2d09ed).
Its wrapped-key FBE v2, metadata key directory and inline crypto flags match
the ROM A/B fstab. Recovery retains its own safe partition exposure.

ROM RTC and PM8150L LED labels are adapted for direct recovery access.
The original authors are credited in the policy commit. Android-only camera,
radio, audio, power, vibrator and DRM HAL declarations are removed from the
recovery VINTF overlay. Boot, health, Keymaster, Gatekeeper and HIDL/keystore
infrastructure remain declared. Recovery uses direct haptics, LEDs, touch and
DRM panel access instead of importing unrelated framework HAL permissions.

Packaging prunes stale overlay-owned VINTF fragments, runs the native Android
17 VINTF assembler, and rejects missing literal init imports or service tools.
The unused generated crypto-service imports are removed; their actual service
definitions remain in Alioth init files. Existing Android 17 policy supplies
ADB, fastbootd, ueventd, logd, storage, USB and snapshot infrastructure rules;
device-specific policy supplies DRM, backlight, haptics, RTC and USB-mode access.

This is source/build coverage of the packaged backend. Hardware-backed key
access, actual SELinux denials and physical service behavior still require the
exact-image phone checks. No claim of full enforcing operation is made.

The aligned candidate passes the recovery rebuild, neverallow and policy type
checks, both native VINTF assemblies, all 21 staged init checks and the full
packaging/installer validation. Artifact hashes above identify this revision.

## Final backend dependency audit

The ramdisk includes native Android 17 `snapuserd` and its disabled, on-demand
service definition. Its rootfs transition retains the enforcing `snapuserd`
domain. Alioth uses dm-user snapshots: upstream kernel guards disable io_uring
and ublk on this 4.19 kernel, without requiring speculative kernel backports.
Actual OTA mapping and merge remain phone checks.

The file manager ZIP command comes from
[the upstream-preserving Info-ZIP fork](https://github.com/pbrp-alioth-a17/android_external_zip).
Its Android 17 build uses the native recovery linker, ZIP64 and UTF-8 support.
The UTF-8 locale falls back from `C.UTF-8` to `en_US.UTF-8` for host compatibility.
Disposable archive checks cover recursive directories, spaces, UTF-8 names,
hidden files and empty directories. Packaging rejects absent or non-executable
ADB, fastbootd, snapshot, crypto, backup, filesystem and file-manager tools.
No test fixtures are committed or installed.

## Android 17 crypto startup verification — 2026-10-12

The initial boot failures were caused by legacy HIDL passthrough lookup,
missing keystore2 AIDL v6 registration, stale incremental runtime libraries,
and an encryption-status helper unmounting data after successful FBE unlock.
That unmount discarded the filesystem keyring and exposed encrypted filenames
through MTP. Status and data-media helpers now preserve an existing data mount.
The removed FDE stub cannot report a successful decryption without doing it.

Recovery opts into binder-backed HIDL lookup with bounded service-manager and
Keymaster registration waits. The latter removes the observed early keystore2
abort while Qualcomm services start. Packaging refreshes native HIDL and
km_compat libraries before checking their dependency closure. Firmware remains
read-only; Alioth does not require a modem keymaster.mdt file.

The earlier crypto-fix Boot image (`0cfe1dca813ecc5f8fe5b9ac2078d7d5d706c09fc97222ea047c88d2fedbdd99`) was temporarily booted on slot A with the
4.19 sm8250 kernel. Windows ADB authorized successfully as uid 2000 with
ro.secure=1 and ro.debuggable=0. Global SELinux was enforcing; only the shared
recovery domain is permissive. Keystore2 remained running, the crash buffer
was empty, and MTP exposed readable Download and DCIM names among 23 storage
entries. No user files were read for this listing, and no credentials, keys or
userdata were rewritten or formatted. Slot B's system/vendor mappings did not
contain valid filesystem headers; this is separate from the recovered FBE
key-lifetime bug. No slot metadata or logical partition contents were modified.

Compilation, Android 17 neverallow/type checks and image/ZIP packaging pass.
5.15 kernels, other credential types, exhaustive UI/theme inspection, OTA installation
and destructive restore operations remain unverified. The signed ZIP was
validated offline, not installed during this final check.


## Settings-aligned Material theme — 2026-10-12

The optional Material theme follows the local EvolutionX Android 17 Settings
and SettingsLib expressive preference implementation: grouped surfaces with
20dp outer corners, 16sp titles, 14sp summaries and 16dp inner padding, scaled
to the recovery canvas. Its home page replaces the original tile grid with
three groups of rows. Recovery operations, console, flashlight and terminal
remain accessible. PBRP Original keeps its existing home layout; external ZIP
themes retain their own resources.

Phone screenshots verified the Material home and General Settings preference
bounds, typography, padding and scrollbar. Earlier phone checks covered the
selector, Advanced, Backup and Reboot layouts in both built-in themes. These
UI checks used the temporary diagnostic recovery with the final native binary
and RAM-staged theme resources. The exact packaged secure image listed above
was then temporarily booted: uid 2000 ADB, ro.secure=1, ro.debuggable=0,
Enforcing, running keystore2, mtp,adb and an empty crash buffer. The pre-test
theme preference was restored, and no partition was flashed. This does not
establish exhaustive page/localization coverage or destructive operation tests.


## Material screen polish verification — 2026-10-12

[UI implementation](https://github.com/pbrp-alioth-a17/android_bootable_recovery/commit/90492023e4b63473d3a44145173c3e551478fc09)
standardizes rounded menu rows, fonts, icon bounds, toolbar navigation,
Explorer dialog geometry, value sliders and swipe confirmations. Reboot uses
compact grouped actions with a separate boot-slot section; Wipe guidance and
Backup Options use consistent surfaces. About retains the original PBRP logo
and displays Android 17 / SDK 37. Original and external theme resources remain
separate from the optional Material renderer.

[CLI connection fix](https://github.com/pbrp-alioth-a17/android_bootable_recovery/commit/0b5f53a4b292524dbf1859a6edbb75c851083091)
passed ten consecutive requests and a stopped-listener test returning failure
after 10.1 seconds. Long-running operation output waits remain unchanged.

Affected native targets and theme generation pass; XML parses, every Material
bitmap is referenced, and image/ZIP validators pass. RAM-staged phone captures
covered About, Advanced, Install/Explorer, Reboot, Wipe/Advanced Wipe, Backup,
Backup Options, Tools, General/Screen/Time Zone/Vibration/Language settings and
the theme selector. A value-slider drag changed the timeout value; the test
value was restored. Both themes were selected through touch. These are safe
UI checks, not destructive wipe, restore, install or slot-change tests.

Final secure Boot SHA-256: `ce16432d7123b9a339ed3af7b50d31e96f9cea69f4b3eeadedb6e635a7ac7739`.
Final installer SHA-256: `d35462cf1809c8b205fab8f1721eba595228e5ed863dc67b28d198ee295b6315`.
The exact secure Boot image was temporarily booted: authorized uid 2000 ADB,
ro.secure=1, ro.debuggable=0, Enforcing, Android 17 / SDK 37, slot A, recovery
and keystore2 running, mtp,adb configured and an empty crash buffer. Production
shell cannot list /sdcard; this is not a new production decryption test. Readable
filenames were seen in diagnostic UI captures. No partition was flashed. The
pre-test Original theme and 60-second timeout were restored before leaving
recovery. Exhaustive localization, other credential types and destructive
operations remain outside this verification.

## Offline UI and portability follow-up — 2026-10-12

The shared [recovery update](https://github.com/pbrp-alioth-a17/android_bootable_recovery/commit/037503712051c31bab8c93377ee7a07fc9cfb065) includes separate commits for Material layout cleanup, the missing language overlay, and portrait theme selection below 720 pixels. Android and SDK are the first aligned Device Information rows; PBRP branding remains present. Console/terminal text no longer receives menu cards. Backup, input, Settings sliders and Time Zone controls have bounded surfaces and consistent contrast.

The [vold update](https://github.com/pbrp-alioth-a17/system_vold/commit/409d3d843978a357b6d0bbde1eac43ffc6b9ebea) validates serialized password records and decodes Weaver slots using the framework's big-endian five-byte format. It retains compatible old/new fields without modifying existing keys. This does not add legacy FDE or establish support for every vendor credential implementation.

Offline checks: affected A17 crypto/UI modules built successfully; 105 pages and 19 templates parsed with no missing static navigation targets, missing images or unused Material images. Six portrait build-selection cases (480×800 through 1440×3120) passed. Disposable address/undefined-behavior sanitizer checks passed for credential prefixes, optional fields, zero-length Weaver handles and truncated files. These checks are not runtime device verification; no test fixtures were committed.

Boot and installer packaging validators passed. New output hashes:
- `recovery_boot.img`: SHA-256 `584bb08914fe5d270dfffc88c4992f849302d4da1e59f0db7d7fb76c839e346c`; 118009856 bytes.
- `recovery.zip`: SHA-256 `e13a610f94355cad87f64315f0263b72102dd398804fecf4b084670f9bd1955b`; 87945275 bytes.

Phone access and flashing were suspended at the user’s request before these changes. The exact new image has not been boot-tested. Other device ports, credential types and screen sizes require their own runtime checks; this update is not a universal production-readiness claim. All work for this follow-up used the standalone recovery tree and the Android 14 recovery reference, not the experimental EVO tree.

## PBRP vendor migration — 2026-10-12

The product and recovery board includes now use the scoped
[PBRP layer on the A17 Lineage base](https://github.com/pbrp-alioth-a17/vendor_lineage/commit/5fbcdc16658619315823b8eecdb24b91a7fc8a33).
The duplicate vendor project is removed from the active manifest and build scan.
Recovery tool packages, versioning, flag namespaces, Soong defaults and
recovery-only policy are retained; the Lineage ROM common product is not
inherited. Current Lineage kernel/header rules, compiler selection and host
tools replace duplicate older infrastructure. Imported source licensing and
provenance are retained. The manifest-owned pb_build wrapper now has a real
source and uses explicit A17 product/release/variant and image arguments.

Offline preservation checks confirm unchanged recovery package lists and policy,
and retention of all PBRP Soong flag exports and module defaults. The completed
Alioth user Boot build passed, including recovery policy compilation. Manifest
parsing and all copy/link source checks pass for the 1,222-project source set.
Boot and installer packaging validation passed. No new test fixtures are
committed. The exact migrated image has not been tested on the phone; EVO and
the device were not accessed for this migration.
- `recovery_boot.img`: SHA-256 `469fff7d2a1d085c300d570f68057874acfe8fb8cf9a0b0ddcac4a7ee52b725c`; 118005760 bytes.
- `recovery.zip`: SHA-256 `22ddde339f5aa80f2489d5d591a377de1e07b2f32a658990fb8896bdb2bceafb`; 87948614 bytes.

## Android 17 dependency audit

System Core is based on LineageOS `lineage-24.0`, with only the explicit PBRP
recovery-boot routing and absent-kernel-attribute ENOENT fixes carried forward.
EvolutionX property spoofing and the unused libkeyutils module are excluded.
Qualcomm twrp-common remains required for Alioth's `qcom_decrypt` and
`qcom_decrypt_fbe` launchers, vendor crypto HAL setup and service cleanup.
Missing OS/patch metadata now fails closed instead of inventing crypto values.

The device ZIP creator remains Info-ZIP: the file manager needs a device-side
archive command; Android's host-side `soong_zip` is not a replacement. Folder
archiving quotes paths and includes hidden files and empty directories.

The Lineage build layer supports source kernels and `TARGET_PREBUILT_KERNEL`.
Optional manifest groups `kernel-platform-515`, `kernel-platform-66`,
`kernel-platform-612` and `kernel-platform-618` expose their upstream kernel
platform dependencies. These are opt-in, not replacements for Alioth's 4.19
kernel. A 5.15+ GKI port also requires matching device/vendor modules, boot
layout and hardware validation. No such port is certified by this offline audit.
FBE and metadata-encryption interfaces are retained; support for every vendor
key format, legacy FDE, or other devices' decryption is not claimed.

Alioth's `m pbrp` uses the same validated image and signed-ZIP packagers as the
manual commands above, rather than the generic both-slot installer:

```sh
export PBRP_ROM=/path/to/matching-ROM.zip
m -j4 pbrp
# Or set PBRP_METADATA_BOOT to a previously matched Boot image, optionally
# PBRP_SECURITY_PATCH=YYYY-MM when its verified patch needs updating.
```

The final dependency audit compiled Boot and Qualcomm decryption helpers,
regenerated Alioth kernel configuration and checked its prebuilt checksums.
Image validation covers init services, ELF dependencies, VINTF, policy,
theme resources and installer payload integrity. These are offline checks;
this revision still needs phone verification before a production release.

Architecture references: [AOSP recovery images](https://source.android.com/docs/core/architecture/bootloader/recovery-images) and [AOSP FBE requirements](https://source.android.com/docs/security/features/encryption/file-based).
