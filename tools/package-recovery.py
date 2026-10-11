#!/usr/bin/env python3
"""Package a final PBRP recovery; never flash."""
import argparse
import os
import re
import hashlib
import gzip
import subprocess
import shutil
import zipfile
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
metadata_source = parser.add_mutually_exclusive_group(required=True)
metadata_source.add_argument("--rom", type=Path, help="Target Alioth ROM ZIP")
metadata_source.add_argument("--metadata-boot", type=Path, help="Previously matched recovery Boot image; retain its OS/patch metadata")
parser.add_argument("--security-patch", help="Verified installed-ROM patch YYYY-MM; override retained Boot metadata")
args = parser.parse_args()
root = Path(__file__).resolve().parents[4]
product = root / "out/target/product/alioth"
staging = product / "recovery/root"
host = root / "out/host/linux-x86/bin"
output = root / "out/release-candidate"
output.mkdir(exist_ok=True)
def ramdisk_target(path):
    for _ in range(32):
        # Normalize lexically, not with Path.resolve(): absolute ramdisk links
        # refer to recovery's root, never the host filesystem.
        path = Path(os.path.normpath(path))
        try:
            relative = path.relative_to(staging)
        except ValueError:
            raise SystemExit(f"Ramdisk symlink escapes staging: {path}")
        current = staging
        found_link = False
        for index, component in enumerate(relative.parts):
            current = current / component
            if current.is_symlink():
                target = current.readlink()
                current = staging / str(target).lstrip("/") if target.is_absolute() else current.parent / target
                path = current.joinpath(*relative.parts[index + 1:])
                found_link = True
                break
        if not found_link:
            return path
    raise SystemExit(f"Ramdisk symlink loop: {path}")

# Android 17's native ramdisk rule no longer stages the private PBRP
# resource overlay. Binary prebuilts remain installed by their build modules.
overlay = root / "device/xiaomi/alioth/recovery/root"
for source in overlay.rglob("*"):
    if source.is_symlink() or not source.is_file():
        continue
    with source.open("rb") as stream:
        if stream.read(4) == b"\x7fELF":
            continue
    if source.suffix == ".md":
        continue
    relative = source.relative_to(overlay)
    # /etc is an absolute ramdisk symlink; never follow it on the build host.
    if relative.parts[0] == "etc":
        relative = Path("system") / relative
    destination = ramdisk_target(staging / relative)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, ramdisk_target(destination))
# The recovery overlay owns these VINTF fragment directories. Remove stale
# declarations left by an incremental build after staging the current set.
for relative in ("vendor/etc/vintf/manifest", "system/etc/vintf/manifest"):
    directory = ramdisk_target(staging / relative)
    expected_fragments = {p.name for p in (overlay / relative).glob("*.xml")}
    for fragment in directory.glob("*.xml"):
        if fragment.name not in expected_fragments:
            ramdisk_target(fragment).unlink()

# Validate merged recovery HAL declarations with this checkout's VINTF parser.
for partition in ("vendor", "system"):
    vintf = ramdisk_target(staging / partition / "etc/vintf")
    manifests = [vintf / "manifest.xml", *sorted((vintf / "manifest").glob("*.xml"))]
    subprocess.run([str(host / "assemble_vintf"), "-i", ":".join(map(str, manifests))],
                   check=True, stdout=subprocess.DEVNULL)

# Refresh production init resources too: a diagnostic boot may have modified
# the staging tree without changing these build inputs.
for source, destination in (
    (root / "bootable/recovery/etc/init.rc", staging / "system/etc/init/hw/init.rc"),
    (root / "bootable/recovery/etc/init.recovery.service22.rc", staging / "init.recovery.service.rc"),
):
    shutil.copy2(source, ramdisk_target(destination))
# Refresh the Qualcomm decryption launcher; its legacy phony install rule
# does not track script changes for an incremental native recovery build.
shutil.copy2(root / "device/qcom/twrp-common/crypto/system/bin/prepdecrypt.sh",
             ramdisk_target(staging / "system/bin/prepdecrypt.sh"))
# Validate service paths inside the ramdisk, never against the build host's
# absolute symlinks. Missing daemons can otherwise leave decryption waiting.

missing_services = []
missing_imports = []
for init_file in staging.rglob("*.rc"):
    if init_file.is_symlink() or not init_file.is_file():
        continue
    for line in init_file.read_text(errors="replace").splitlines():
        fields = line.split()
        if len(fields) == 2 and fields[0] == "import" and "$" not in fields[1] and not init_file.name.startswith("ueventd"):
            imported = ramdisk_target(staging / fields[1].lstrip("/"))
            if not imported.exists():
                missing_imports.append((str(init_file.relative_to(staging)), fields[1]))
        if len(fields) >= 3 and fields[0] == "service" and fields[2].startswith("/") and "$" not in fields[2]:
            binary = ramdisk_target(staging / fields[2].lstrip("/"))
            if not binary.is_file() or not binary.stat().st_mode & 0o111:
                missing_services.append((str(init_file.relative_to(staging)), fields[1], fields[2]))
            elif binary.read_bytes()[:2] == b"#!":
                interpreter = binary.read_text().splitlines()[0][2:].strip().split()[0]
                shell = ramdisk_target(staging / interpreter.lstrip("/"))
                if not interpreter.startswith("/") or not shell.is_file() or not shell.stat().st_mode & 0o111:
                    missing_services.append((str(init_file.relative_to(staging)), fields[1], interpreter))
if missing_imports:
    raise SystemExit(f"Missing recovery init imports: {missing_imports}")
if missing_services:
    raise SystemExit(f"Missing or non-executable recovery service tools: {missing_services}")
# Tools required by the approved recovery backend, beyond ZIP installation.
backend_tools = (
    "adbd fastbootd snapuserd update_engine_sideload keystore2 qseecomd "
    "android.hardware.keymaster@4.0-service-qti "
    "android.hardware.gatekeeper@1.0-service-qti "
    "magiskboot pigz zip bu make_f2fs fsck.f2fs e2fsck mke2fs resize2fs logcat dmesg"
).split()
for tool in backend_tools:
    binary = ramdisk_target(staging / "system/bin" / tool)
    if not binary.is_file() or not binary.stat().st_mode & 0o111:
        raise SystemExit(f"Missing or non-executable recovery backend tool: {tool}")

# These applets are required by the approved Boot ramdisk installer.
installer_tools = "getprop unzip sha256sum dd blockdev head wc cut mktemp sync chmod mkdir cp cmp rm id sh".split()
missing_tools = []
for tool in installer_tools:
    binary = ramdisk_target(staging / "system/bin" / tool)
    if not binary.is_file() or not binary.stat().st_mode & 0o111:
        missing_tools.append(tool)
if missing_tools:
    raise SystemExit(f"Missing recovery installer tools: {missing_tools}")
# Fail rather than silently boot a stale theme from an incremental build.
for source, destination in (
    (root / "bootable/recovery/gui/theme/common/portrait.xml", staging / "twres/portrait.xml"),
    (root / "bootable/recovery/gui/theme/portrait_hdpi/extras.xml", staging / "twres/extras.xml"),
):
    if source.read_bytes() != destination.read_bytes():
        raise SystemExit(f"Stale recovery resource: {destination}; rebuild the theme before packaging")

# ui.xml contains a generated theme version; compare its complete contents
# after the same substitution performed by gui/Android.mk.
version_header = (root / "bootable/recovery/variables.h").read_text()
theme_version = re.search(r"^#define TW_THEME_VERSION (\d+)$", version_header, re.MULTILINE)
if not theme_version:
    raise SystemExit("Missing recovery theme version")
ui_source = (root / "bootable/recovery/gui/theme/portrait_hdpi/ui.xml").read_text()
ui_expected = ui_source.replace("{themeversion}", theme_version.group(1))
if ui_expected != (staging / "twres/ui.xml").read_text():
    raise SystemExit("Stale recovery ui.xml; rebuild the theme before packaging")

if args.rom:
    with zipfile.ZipFile(args.rom) as archive:
        metadata = dict(line.split("=", 1) for line in archive.read("META-INF/com/android/metadata").decode().splitlines() if "=" in line)
    if not {"alioth", "aliothin"}.intersection(metadata.get("pre-device", "").split(",")):
        raise SystemExit("ROM does not target Alioth")
    os_version = metadata["post-build"].split(":", 1)[1].split("/", 1)[0]
    patch_level = metadata["post-security-patch-level"][:7]
else:
    import struct
    with args.metadata_boot.open("rb") as image:
        header = image.read(44)
    if len(header) != 44 or header[:8] != b"ANDROID!" or struct.unpack_from("<I", header, 40)[0] != 3:
        raise SystemExit("Metadata source must be a header-v3 Android Boot image")
    version = struct.unpack_from("<I", header, 16)[0]
    os_version = f"{(version >> 25) & 127}.{(version >> 18) & 127}.{(version >> 11) & 127}"
    month = version & 15
    if not version or not 1 <= month <= 12:
        raise SystemExit("Metadata source has missing/invalid OS or patch metadata")
    patch_level = f"{2000 + ((version >> 4) & 127):04d}-{month:02d}"
if args.security_patch:
    if not args.metadata_boot or not re.fullmatch(r"20[0-9]{2}-(0[1-9]|1[0-2])", args.security_patch):
        raise SystemExit("--security-patch requires --metadata-boot and valid YYYY-MM")
    patch_level = args.security_patch
# Incremental relink modules do not track all native library output changes.
# Stage the exact linked recovery backends before auditing the ramdisk.
for library in ("libaosprecovery.so", "libminuitwrp.so"):
    shutil.copy2(product / "system/lib64" / library, ramdisk_target(staging / "system/lib64" / library))
# libion's implementation is selected by the product; incremental relinking
# must not retain the previous Android 17 stub after that selection changes.
for libdir in ("lib", "lib64"):
    native = product / "system" / libdir / "libion.so"
    staged = staging / "system" / libdir / "libion.so"
    if staged.exists():
        if not native.is_file():
            raise SystemExit(f"Missing native libion output: {native}")
        shutil.copy2(native, ramdisk_target(staged))
# The legacy relinker previously replaced the recovery variant with the
# system libvintf. Refresh its exact native recovery build output as well.
vintf_outputs = list((root / "out/soong/.intermediates/system/libvintf/libvintf").glob(
    "android_recovery_arm64*_shared/libvintf.so"))
if len(vintf_outputs) != 1:
    raise SystemExit("Expected one linked arm64 recovery libvintf output; rebuild libvintf.recovery")
shutil.copy2(vintf_outputs[0], ramdisk_target(staging / "system/lib64/libvintf.so"))
# Native bootstrap binaries, including hwservicemanager, retain this ELF path.
# Recovery uses the same staged Bionic linker before any installed-OS mounts.
bootstrap = ramdisk_target(staging / "system/bin/bootstrap")
bootstrap.mkdir(parents=True, exist_ok=True)
for name in ("linker", "linker64"):
    target = ramdisk_target(staging / "system/bin" / name)
    if not target.is_file():
        continue
    link = bootstrap / name
    if link.is_symlink():
        link.unlink()
    elif link.exists():
        raise SystemExit(f"Unexpected bootstrap linker file: {link}")
    link.symlink_to("../" + name)
    legacy = ramdisk_target(staging / "sbin") / name
    if not legacy.exists() and not legacy.is_symlink():
        legacy.symlink_to("/system/bin/" + name)

# Fail packaging if a staged executable or library lacks an ABI-matching provider.
# Inspect staged ELF files using the checkout compiler tools, rather than install aliases.
readelf = root / "prebuilts/clang/host/linux-x86/clang-r596125/bin/llvm-readelf"
# Android 17 gives protobuf a versioned SONAME. Refresh lpdump's exact
# linked dependency names instead of copying the removed unversioned path.
lpdump = staging / "system/lib64/liblpdump.so"
if lpdump.is_file():
    dynamic = subprocess.check_output([str(readelf), "-d", str(lpdump)], text=True)
    dependencies = re.findall(r"\(NEEDED\).*?\[(.*?)\]", dynamic)
    libraries = ["libfs_mgr_binder.so", "libsnapshot.so"]
    libraries.extend(name for name in dependencies if name.startswith("libprotobuf-cpp-full") and "/" not in name)
    for library in libraries:
        shutil.copy2(product / "system/lib64" / library, ramdisk_target(staging / "system/lib64" / library))
elf_dependencies = []
providers = set()
exports = {}
imports = []
provider_paths = {}
for candidate in staging.rglob("*"):
    if "first_stage_ramdisk" in candidate.relative_to(staging).parts:
        continue
    if candidate.is_symlink() or not candidate.is_file():
        continue
    with candidate.open("rb") as source:
        header = source.read(20)
    if header[:4] != b"\x7fELF":
        continue
    program_headers = subprocess.check_output([str(readelf), "-l", str(candidate)], text=True)
    match = re.search(r"Requesting program interpreter: ([^\]]+)", program_headers)
    if match:
        interpreter = match.group(1)
        loader = ramdisk_target(staging / interpreter.lstrip("/"))
        if not interpreter.startswith("/") or not loader.is_file() or not loader.stat().st_mode & 0o111:
            raise SystemExit(f"Missing ELF interpreter for {candidate.relative_to(staging)}: {interpreter}")
    abi = (header[4], header[18:20])
    dynamic = subprocess.check_output([str(readelf), "-d", str(candidate)], text=True)
    runtime_dirs = {"system/lib", "system/lib64", "vendor/lib", "vendor/lib64",
                    "vendor/lib/hw", "vendor/lib64/hw", "sbin"}
    if str(candidate.parent.relative_to(staging)) in runtime_dirs:
        providers.add((abi, candidate.name))
        provider_paths.setdefault((abi, candidate.name), candidate)
    for soname in re.findall(r"\(SONAME\).*?\[(.*?)\]", dynamic):
        if str(candidate.parent.relative_to(staging)) in runtime_dirs:
            providers.add((abi, soname))
            provider_paths.setdefault((abi, soname), candidate)
    elf_dependencies.append((candidate, abi, re.findall(r"\(NEEDED\).*?\[(.*?)\]", dynamic)))
    symbols = subprocess.check_output([str(readelf), "--dyn-syms", "--wide", str(candidate)], text=True)
    for line in symbols.splitlines():
        fields = line.split()
        if len(fields) < 8 or not fields[0].endswith(":"):
            continue
        symbol = fields[7].replace("@@", "@")
        if fields[6] == "UND" and fields[4] == "GLOBAL":
            imports.append((candidate, abi, symbol))
        elif fields[6] != "UND" and fields[4] in ("GLOBAL", "WEAK") and fields[5] in ("DEFAULT", "PROTECTED"):
            exports.setdefault(candidate, set()).add(symbol)
            if "@@" in fields[7]:
                exports[candidate].add(fields[7].split("@@")[0])
missing = [(str(candidate.relative_to(staging)), dependency)
           for candidate, abi, dependencies in elf_dependencies
           for dependency in dependencies if (abi, dependency) not in providers]
if missing:
    raise SystemExit(f"Missing recovery runtime library providers: {missing}")
dependency_map = {candidate: dependencies for candidate, abi, dependencies in elf_dependencies}
def runtime_exports(candidate, abi):
    visited = set()
    pending = [candidate]
    available = set()
    while pending:
        current = pending.pop()
        if current in visited:
            continue
        visited.add(current)
        available.update(exports.get(current, set()))
        for dependency in dependency_map.get(current, []):
            provider = provider_paths.get((abi, dependency))
            if provider is not None:
                pending.append(provider)
    return available
available_exports = {(candidate, abi): runtime_exports(candidate, abi)
                     for candidate, abi, dependencies in elf_dependencies}
unresolved = [(str(candidate.relative_to(staging)), symbol)
              for candidate, abi, symbol in imports
              if symbol not in available_exports[(candidate, abi)]]

if unresolved:
    raise SystemExit(f"Unresolved strong recovery runtime symbols: {unresolved}")

# Do not publish ramdisks left behind by an adbd-root diagnostic build.
properties = dict(line.split("=", 1) for line in (staging / "prop.default").read_text().splitlines()
                  if "=" in line and not line.startswith("#"))
if properties.get("ro.secure") != "1" or properties.get("ro.debuggable") != "0":
    raise SystemExit("Production packaging requires ro.secure=1 and ro.debuggable=0")

policy = staging / "sepolicy"
domains = set(subprocess.check_output([str(host / "sepolicy-analyze"), str(policy), "permissive"], text=True).split())
expected = {"recovery"}
if domains != expected:
    raise SystemExit(f"Unexpected permissive domains: {sorted(domains)}")
# Android 17's ramdisk rule does not generate PBRP's Flash Current inventory.
# Generate it from the exact validated staging tree, including both manifests.
inventory = staging / "ramdisk-files.txt"
checksums = staging / "ramdisk-files.sha256sum"
names = {str(path.relative_to(staging)) for path in staging.rglob("*")}
names.update({inventory.name, checksums.name})
inventory.write_text(".\n" + "\n".join(sorted(names)) + "\n")
entries = []
for name in sorted(names):
    source = staging / name
    if name == checksums.name or source.is_symlink() or not source.is_file():
        continue
    entries.append(hashlib.sha256(source.read_bytes()).hexdigest() + "  " + name)
checksums.write_text("\n".join(entries) + "\n")
cpio = subprocess.check_output([str(host / "mkbootfs"), "-d", str(product), str(staging)])
ramdisk = output / "ramdisk.gz"
ramdisk.write_bytes(gzip.compress(cpio, mtime=0))
image = output / "recovery_boot.img"
subprocess.run([str(host / "mkbootimg"), "--kernel", str(product / "kernel"), "--ramdisk", str(ramdisk), "--header_version", "3", "--os_version", os_version, "--os_patch_level", patch_level, "--cmdline", "twrpfastboot=1 androidboot.pbrp=1 printk.devkmsg=on", "--output", str(image)], check=True)
ramdisk.unlink()
board_config = (root / "device/xiaomi/alioth/BoardConfig.mk").read_text()
boot_limit = re.search(r"^BOARD_BOOTIMAGE_PARTITION_SIZE\s*:=\s*(\d+)$", board_config, re.MULTILINE)
if not boot_limit or image.stat().st_size > int(boot_limit.group(1)):
    image.unlink()
    raise SystemExit("Recovery Boot image exceeds the configured partition or its size is undefined")
print(f"PBRP RECOVERY: {image}; OS {os_version}, patch {patch_level}")
