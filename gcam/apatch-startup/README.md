**English** | [Español](README.es.md)

# BSG V32 ? APatch system module 0.7.0

Optional system installation for X6810-GL. BSG V32 and telephoto OIS were tested and work correctly on Android 16 GSI with [the recommended profile](../../profiles/README.md). Any compatible external GCam can instead be installed normally; this module is independent of RAW.

The original signed APK is retained in `payload/MGC_9.7.047_V32_MGC.apk` and preserved unchanged in the ZIP. The 21 ARM64 libraries are extracted separately; only `libgcastartup.so` is replaced by the verified cache-fix library. Historical 0.5.0 DEX/panel patches are not applied.

## Build and install

From the repository root, run `python scripts/build.py`, install the generated ZIP through APatch and reboot. The builder validates the original APK SHA-256, cache-library SHA-256, 21-library inventory, permission XML and ZIP. The installer rejects a different installed APK version. See [installation and recovery](../../docs/INSTALLATION.md).

The installer admits API 30+; Android 11 behavior is unverified. Device evidence is Android 16 GSI, and this repackaging has not had new hardware validation. Import the recommended XML manually; it is not applied at boot.

## Permissions and mounting

The module installs `system/priv-app/X6810GCam/X6810GCam.apk`, supplies libraries and runtime-permission XML, and allows only the declared privileged `INSTALL_PACKAGE_UPDATES` permission. Initial grants cover the 11 declared runtime permissions as supported by the Android version. Special accesses include `MANAGE_EXTERNAL_STORAGE`, `WRITE_SETTINGS` and Do Not Disturb policy access. Missing manifest permissions are not invented. The app retains its original signature and does not become platform-signed.

An existing identical user APK can remain in `/data/app` with system/updated-system/privileged flags. Its data is preserved, and the native fix is mounted over the verified original library after source and ownership checks. Updates and data are not deleted to force a path change. Review `customize.sh`, `service.sh`, `activate.sh`, `permissions.sh` and `uninstall.sh` for exact operations.

Disable/remove `x6810_gcam_startup` and reboot to remove the overlay. Existing app data and some special-access grants can remain; revoke them in Settings if desired. [Disclaimer](../../DISCLAIMER.md) and [third-party notices](../../THIRD_PARTY_NOTICES.md).
