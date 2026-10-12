**English** | [Español](es/INSTALLATION.md)

# External app or optional system module

Any compatible external GCam can be installed as a normal APK without this system module. The RAW/OIS/HD48 and flash modules do not require a particular app. BSG `MGC_9.7.047_V32_MGC.apk` (`com.android.MGC_9_7_047`) was tested and works perfectly with [the recommended V32 profile](../profiles/README.md) on Android 16 GSI. Telephoto OIS was tested and works correctly.

For the optional system installation, run `python scripts/build.py`, check `SHA256SUMS.txt`, install `x6810-gcam-system-0.7.0.zip` through APatch and reboot. The builder uses the retained original signed APK by default, or accepts that same APK with `--apk`. Other ports can be installed manually but are not accepted by this pinned system builder.

PackageManager scans the priv-app overlay at boot. The module exposes 21 ARM64 libraries with the verified cache replacement for `libgcastartup.so`, preserves app data, verifies installed APK identity, and configures permissions. Runtime permissions are version-dependent; special accesses include all-files storage, settings modification and Do Not Disturb policy access. See the [module details](../gcam/apatch-startup/README.md). The original APK signature is preserved; it is not platform-signed.

The V32 XML is delivered separately and imported manually; installation does not apply it automatically. Disable/remove `x6810_gcam_startup` and reboot to remove the overlay. Existing data is not automatically deleted; special accesses can persist and can be revoked in Android Settings.

The installer accepts API 30+, but only Android 16 GSI has device evidence. Android 11 APK, permission, ABI and boot behavior remain unverified. This documentation revision did not run new mobile tests. Install [RAW/OIS/HD48 or flash](https://github.com/SRE-0/infinix_x6810_raw) separately.
