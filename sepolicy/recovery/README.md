# Alioth recovery policy

Device policy is compiled through BOARD_VENDOR_SEPOLICY_DIRS. Hardware
permissions are enclosed in recovery_only: they grant nothing to Android HALs.

Labels verified on the historical Android 14 recovery:
- /dev/dri/card0: vendor_alioth_recovery_drm_device (DRM UI)
- panel0-backlight/brightness: vendor_alioth_recovery_backlight
- AW8697 activate, activate_mode, duration: vendor_alioth_recovery_haptics

The physical sysfs paths were measured on kernel ac2a025a05e6. Do not grant
write access to all sysfs or copy ROM SELinux policy wholesale into recovery.
Gain/calibration/register interfaces are deliberately not exposed here.

Historical Android 14 build and neverallow checks passed. In a temporary globally permissive audit,
the labels applied and previous recovery DRM/backlight/RTC startup denials
were absent. Physical menu navigation, brightness and haptics passed user testing
with the device policy implementation. Password decryption, menus, brightness and haptics passed
on the October 7 packaged image with global SELinux Enforcing. Shell diagnostic denials are not production
requirements.

This is targeted device policy, not a fully enforcing PBRP conversion.
Only the shared recovery domain remains permissive. General property
enumeration, co-located services, APEX/filesystem operations and installation
need a separate full enforcing-policy audit. Do not claim they were solved.

Historical infrastructure enforcement is recorded in ENFORCING_AUDIT.md.
The Android 17 port requires its own exact-image runtime verification. The release
packager accepts only recovery as permissive; widening this set requires
explicit review. USB mode labeling is restricted to Alioth's physical
/sys/devices/platform/soc/a600000.ssusb/mode node.

## Android 17 offline validation

The current port uses the Android 17 / LineageOS 24 platform policy, including
versioned recovery genfs labels. Recovery policy compilation, neverallow checks,
`sepolicy_test`, `sepolicy_dev_type_test`, and staged file/property/Binder/HIDL
context validation pass. The redundant PBRP adbd `setcurrent` rule is removed;
the native platform rule and recovery shell transition remain available.

The production source restores normal init SELinux enforcement. The compiled
policy permits only the approved shared `recovery` domain to be permissive.
The earlier globally permissive image was diagnostic and is not the production
candidate. Full enforcement of the shared recovery domain is not claimed.

Native init verification passes for all 20 staged init scripts after removing
the obsolete `install_keyring` action. Fscrypt v2 key installation remains in
recovery vold through filesystem ioctls. Executable/service dependency audits
cover the decryption launcher, HIDL manager, charger and lpdump runtime closure.
These are offline results; decryption, USB authorization and enforcing-image
hardware behavior still require exact-image phone verification before release.
