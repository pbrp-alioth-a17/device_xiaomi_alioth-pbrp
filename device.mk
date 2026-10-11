# SPDX-License-Identifier: Apache-2.0
LOCAL_PATH := device/xiaomi/alioth
PRODUCT_SHIPPING_API_LEVEL := 30
PRODUCT_USE_DYNAMIC_PARTITIONS := true
$(call inherit-product, $(SRC_TARGET_DIR)/product/virtual_ab_ota.mk)
# Recovery prop.default must expose this even without mounting vendor.
PRODUCT_PROPERTY_OVERRIDES += ro.virtual_ab.enabled=true
# Recovery has no Android framework authorization dialog. The recovery-only
# switch is honored by adbd only on an unlocked bootloader or a debug build.
PRODUCT_PROPERTY_OVERRIDES += ro.adb.secure.recovery=false
PRODUCT_BUILD_SUPER_PARTITION := false
PRODUCT_PACKAGES += qcom_decrypt qcom_decrypt_fbe


# Android 17 port resolves required recovery modules explicitly.

PRODUCT_PACKAGES += alioth_recovery_0 alioth_recovery_1 alioth_recovery_2 alioth_recovery_3 alioth_recovery_4 alioth_recovery_5 alioth_recovery_6 alioth_recovery_7 alioth_recovery_8 alioth_recovery_9 alioth_recovery_10 alioth_recovery_11 alioth_recovery_12 alioth_recovery_13 alioth_recovery_14 alioth_recovery_15 alioth_recovery_16 alioth_recovery_17 alioth_recovery_18 alioth_recovery_19 alioth_recovery_20 alioth_recovery_21 alioth_recovery_22 alioth_recovery_23 alioth_recovery_24 alioth_recovery_25 alioth_recovery_26 alioth_recovery_27 alioth_recovery_28 alioth_recovery_29 alioth_recovery_30 alioth_recovery_31
# PBRP copies recovery/root as the private recovery overlay.

# Official PBRP recovery-library inclusion/relink convention.
PRODUCT_SOONG_NAMESPACES += vendor/qcom/opensource/commonsys-intf/display
TARGET_RECOVERY_DEVICE_MODULES += android.system.suspend-V1-ndk android.hardware.gatekeeper@1.0 android.hardware.keymaster@4.0 android.hardware.keymaster@4.1 android.system.wifi.keystore@1.0 libion libxml2 libdisplayconfig.qti vendor.display.config@1.0 vendor.display.config@2.0
TW_RECOVERY_ADDITIONAL_RELINK_LIBRARY_FILES += $(TARGET_OUT_SHARED_LIBRARIES)/libion.so $(TARGET_OUT_SHARED_LIBRARIES)/libxml2.so $(TARGET_OUT_VENDOR_SHARED_LIBRARIES)/libdisplayconfig.qti.so $(TARGET_OUT_SYSTEM_EXT_SHARED_LIBRARIES)/vendor.display.config@1.0.so $(TARGET_OUT_SYSTEM_EXT_SHARED_LIBRARIES)/vendor.display.config@2.0.so

TW_RECOVERY_ADDITIONAL_RELINK_LIBRARY_FILES += $(TARGET_OUT_SHARED_LIBRARIES)/android.system.suspend-V1-ndk.so

# Alioth UFS slot control, following the maintained OrangeFox device tree.
PRODUCT_SOONG_NAMESPACES += device/xiaomi/alioth hardware/qcom-caf/bootctrl
PRODUCT_PACKAGES += bootctrl.kona.recovery android.hardware.boot@1.1-impl-qti.recovery
PRODUCT_PROPERTY_OVERRIDES += vendor.gatekeeper.disable_spu=true vendor.usb.use_ffs_mtp=1

# Device-specific GUI capabilities; never applies to other PBRP targets.
PRODUCT_PROPERTY_OVERRIDES += ro.pbrp.alioth_safe_ui=1
PRODUCT_PROPERTY_OVERRIDES += ro.pbrp.display_refresh_rate=120

# Required for compressed/userspace Virtual A/B snapshot mappings.
PRODUCT_PACKAGES += snapuserd.recovery
# File manager ZIP creation uses the upstream PBRP archiver.
PRODUCT_PACKAGES += zip
