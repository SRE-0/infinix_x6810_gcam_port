#!/system/bin/sh
[ "$(getprop ro.product.device)" = Infinix-X6810 ] || abort "Infinix X6810 required"
[ "$(getprop ro.build.version.sdk)" -ge 30 ] || abort "Android 11 or newer required"

# Refuse an incompatible installed APK rather than silently shadowing it.
PACKAGE=com.android.MGC_9_7_047
EXPECTED=132e18273b3aafdb93e851f5db88156bd4f82c5032ad8de6594fa5a49ea6fe89
PAYLOAD="$MODPATH/system/priv-app/X6810GCam/X6810GCam.apk"
[ "$(sha256sum "$PAYLOAD" | awk '{print $1}')" = "$EXPECTED" ] || abort "Invalid original APK payload"
installed=$(pm path "$PACKAGE" | sed -n 's/^package://p')
if [ -n "$installed" ]; then
    [ "$(printf '%s\n' "$installed" | wc -l)" -eq 1 ] || abort "Split APK not supported"
    hash=$(sha256sum "$installed" | awk '{print $1}')
    case "$hash" in
        "$EXPECTED"|2218c653d91482b377877014bbc22610cb386c30465c4b831c944299f0ea1b83) ;;
        *) abort "Unsupported installed GCam; preserve it and install the original version first" ;;
    esac
fi
# APatch mounts priv-app and permission XML before PackageManager scans apps.
rm -f "$MODPATH/skip_mount"
set_perm_recursive "$MODPATH/system" 0 0 0755 0644 u:object_r:system_file:s0
for script in activate.sh service.sh uninstall.sh permissions.sh; do
    set_perm "$MODPATH/$script" 0 0 0755
done
set_perm "$MODPATH/customize.sh" 0 0 0755
