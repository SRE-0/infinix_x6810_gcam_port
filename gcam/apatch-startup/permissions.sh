#!/system/bin/sh
set -u
MODDIR=${0%/*}
PACKAGE=com.android.MGC_9_7_047
sdk=$(getprop ro.build.version.sdk)
# Wait for PackageManager without a fixed startup delay.
attempt=0
while ! pm path "$PACKAGE" | grep -q '^package:'; do
    attempt=$((attempt + 1))
    [ "$attempt" -lt 30 ] || { echo 'PackageManager did not register GCam'; exit 1; }
    sleep 2
done
pm list packages -s | grep -qx "package:$PACKAGE" || { echo 'System classification missing'; exit 1; }
uid=$(pm list packages -U "$PACKAGE" | sed -n 's/.*uid://p')
[ -n "$uid" ] || exit 1
fingerprint="0.7.0:$uid:$sdk"
# Preserve subsequent user revocations. Retry a failed initial grant next boot.
if [ "$(cat "$MODDIR/.permissions-granted" 2>/dev/null || true)" = "$fingerprint" ]; then
    echo 'Initial permission grant already completed; user choices preserved'
    exit 0
fi
failed=0
grant() {
    if pm grant --user 0 "$PACKAGE" "$1"; then
        echo "Granted: $1"
    else
        echo "FAILED: $1"
        failed=1
    fi
}
for permission in CAMERA RECORD_AUDIO ACCESS_COARSE_LOCATION ACCESS_FINE_LOCATION READ_EXTERNAL_STORAGE WRITE_EXTERNAL_STORAGE; do
    grant "android.permission.$permission"
done
if [ "$sdk" -ge 33 ]; then
    for permission in NEARBY_WIFI_DEVICES READ_MEDIA_IMAGES READ_MEDIA_VIDEO POST_NOTIFICATIONS; do
        grant "android.permission.$permission"
    done
fi
[ "$sdk" -lt 34 ] || grant android.permission.READ_MEDIA_VISUAL_USER_SELECTED
# Special accesses require app-ops / NotificationManager in addition to manifest permissions.
for op in MANAGE_EXTERNAL_STORAGE WRITE_SETTINGS; do
    if cmd appops set --user 0 --uid "$PACKAGE" "$op" allow &&
        cmd appops set --user 0 "$PACKAGE" "$op" allow &&
        cmd appops get --user 0 "$PACKAGE" "$op" | grep -q "$op: allow"; then
        echo "Special access allowed: $op"
    else
        echo "FAILED special access: $op"
        failed=1
    fi
done
if cmd notification allow_dnd "$PACKAGE" 0; then
    echo 'DND policy access allowed'
else
    failed=1
fi
# Framework supplies normal/signature-self permissions; privapp XML supplies this one.
if dumpsys package "$PACKAGE" | awk '
    /Hidden system packages:/ {hidden=1}
    !hidden && /android.permission.INSTALL_PACKAGE_UPDATES: granted=true/ {found=1}
    END {exit !found}'; then
    echo 'Privileged INSTALL_PACKAGE_UPDATES verified'
else
    echo 'FAILED: privileged permission missing; check priv-app mount/XML and reboot'
    failed=1
fi
[ "$failed" -eq 0 ] || exit 1
printf '%s\n' "$fingerprint" > "$MODDIR/.permissions-granted"
echo 'Initial permission setup complete'
