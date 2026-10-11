# Android 17 source setup

Use the [pbrp-alioth-a17 manifest](https://github.com/pbrp-alioth-a17/manifest)
to obtain the matching platform, recovery, vendor configuration, decryption
adapter, policy and Alioth device tree. The manifest pins the source revisions.

The old Android 14 patch replay files have been retired. Their approved behavior
is retained in the recovery and vendor repositories, with original authorship
in Git history. Do not apply that series to the Android 17 platform.

Build and packaging instructions are in the device tree [README](../README.md).
The current Android 17 port remains under build and runtime validation.
