#!/system/bin/sh
# Prepare only the active slot's read-only Qualcomm firmware for recovery crypto.
fail() {
    echo "Alioth crypto preparation: $*" > /dev/kmsg
    exit 1
}
setprop alioth.crypto.ready 0
slot=$(getprop ro.boot.slot_suffix)
case "$slot" in _a|_b) ;; *) fail "invalid slot suffix" ;; esac
modem=/dev/block/bootdevice/by-name/modem$slot
count=0
while [ ! -b "$modem" ] || [ ! -c /dev/ion ] || [ ! -c /dev/qseecom ]; do
    [ "$count" -lt 10 ] || fail "firmware or crypto device unavailable"
    sleep 1
    count=$((count + 1))
done
mkdir -p /vendor/firmware_mnt || fail "cannot create firmware mount point"
chmod 0755 /vendor || fail "cannot allow firmware parent traversal"
mounted_source=$(awk '$2 == "/vendor/firmware_mnt" {print $1}' /proc/mounts)
if [ -n "$mounted_source" ]; then
    [ "$(readlink -f "$mounted_source")" = "$(readlink -f "$modem")" ] || fail "firmware mounted from another partition"
    for directory in /vendor/firmware_mnt /vendor/firmware_mnt/image; do
        [ "$(stat -c '%u:%g:%a' "$directory")" = "1000:1000:550" ] || fail "unexpected firmware directory permissions"
    done
    [ "$(stat -c '%u:%g:%a' /vendor/firmware_mnt/image/keymaster.mdt)" = "1000:1000:440" ] || fail "unexpected firmware file permissions"
    awk '$2 == "/vendor/firmware_mnt" && $3 == "vfat" && $4 ~ /(^|,)ro(,|$)/ {found=1} END {exit !found}' /proc/mounts || fail "firmware mount is not read-only vfat"
else
    mount -t vfat -o ro,uid=1000,gid=1000,dmask=227,fmask=337 "$modem" /vendor/firmware_mnt || fail "cannot mount firmware"
fi
[ -r /vendor/firmware_mnt/image/keymaster.mdt ] || fail "keymaster firmware unavailable"
setprop alioth.crypto.ready 1
