# SPDX-License-Identifier: Apache-2.0
$(call inherit-product, $(SRC_TARGET_DIR)/product/core_64_bit.mk)
$(call inherit-product, $(SRC_TARGET_DIR)/product/base.mk)
$(call inherit-product, device/xiaomi/alioth/device.mk)
$(call inherit-product, vendor/lineage/config/recovery.mk)
PRODUCT_NAME := pb_alioth
PRODUCT_DEVICE := alioth
PRODUCT_BRAND := POCO
PRODUCT_MANUFACTURER := Xiaomi
PRODUCT_MODEL := POCO F3

# Use the metadata-aware, active-Boot-only Alioth installer.
PBRP_PACKAGE_SCRIPT := device/xiaomi/alioth/tools/package-pbrp.sh
