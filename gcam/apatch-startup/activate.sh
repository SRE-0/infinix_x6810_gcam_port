#!/system/bin/sh
set -eu
MODDIR=${0%/*}
PACKAGE=com.android.MGC_9_7_047
SYSTEM_APP=/system/priv-app/X6810GCam/X6810GCam.apk
APK="$MODDIR/system/priv-app/X6810GCam/X6810GCam.apk"
NATIVE="$MODDIR/system/priv-app/X6810GCam/lib/arm64/libgcastartup.so"
ORIGINAL=132e18273b3aafdb93e851f5db88156bd4f82c5032ad8de6594fa5a49ea6fe89
NATIVE_ORIGINAL=76966e7c150dfcb2795ea5b2119827a7e90b13d8c03035dbc4de583d9d12eaa6
NATIVE_PATCHED=64cfcb3f598cdf3e75875bdd4cb8e8775a6763be15c3d2240d1d7ee0656f053a
digest() { sha256sum "$1" | awk '{print $1}'; }
mounted() { awk -v p="$1" '$5==p {found=1} END {exit !found}' /proc/self/mountinfo; }
target=$(pm path "$PACKAGE" | sed -n 's/^package://p')
[ -n "$target" ] && [ "$(printf '%s\n' "$target" | wc -l)" -eq 1 ] || {
    echo 'Package absent or split; reboot after installing the module'; exit 1;
}
case "$target" in
    "$SYSTEM_APP") mode=system ;;
    /data/app/*/com.android.MGC_9_7_047-*/base.apk) mode=updated-system ;;
    *) echo "Unexpected package path: $target"; exit 1 ;;
esac
native_target="${target%/*}/lib/arm64/libgcastartup.so"
owns_native_mount() {
    mounted "$native_target" && [ "$(digest "$native_target")" = "$NATIVE_PATCHED" ] &&
        [ "$(stat -c %d:%i "$native_target")" = "$(stat -c %d:%i "$NATIVE")" ];
}
case "${1:-status}" in
    apply)
        [ ! -f "$MODDIR/disable" ] && [ ! -f "$MODDIR/remove" ] || exit 0
        [ "$(getprop ro.product.device)" = Infinix-X6810 ] || exit 1
        [ "$(digest "$APK")" = "$ORIGINAL" ] || { echo 'APK payload hash mismatch'; exit 1; }
        [ "$(digest "$NATIVE")" = "$NATIVE_PATCHED" ] || { echo 'Native payload hash mismatch'; exit 1; }
        [ "$(digest "$SYSTEM_APP")" = "$ORIGINAL" ] || { echo 'Priv-app overlay absent; reboot required'; exit 1; }
        pm list packages -s | grep -qx "package:$PACKAGE" || { echo 'GCam is not a system app'; exit 1; }
        [ "$(digest "$target")" = "$ORIGINAL" ] || { echo 'Unsupported APK update; leaving it intact'; exit 1; }
        if [ "$mode" = updated-system ]; then
            if mounted "$native_target"; then
                owns_native_mount || { echo 'Native mount belongs to another owner'; exit 1; }
            else
                [ "$(digest "$native_target")" = "$NATIVE_ORIGINAL" ] || { echo 'Unsupported native library'; exit 1; }
                am force-stop "$PACKAGE"
                mount --bind "$NATIVE" "$native_target"
                if ! owns_native_mount; then
                    umount -l "$native_target"
                    echo 'Native mount verification failed'; exit 1
                fi
            fi
        fi
        [ "$(digest "$native_target")" = "$NATIVE_PATCHED" ] || { echo 'Active native hash mismatch'; exit 1; }
        echo "Original signed APK active ($mode): $ORIGINAL"
        echo "Native cache fix active: $NATIVE_PATCHED"
        # No repeated full ART compilation on every boot. Only compile a new path/build.
        fingerprint="$target:$ORIGINAL:$NATIVE_PATCHED:$(getprop ro.build.fingerprint)"
        if [ "$(cat "$MODDIR/.compiled" 2>/dev/null || true)" != "$fingerprint" ]; then
            result=$(cmd package compile -m speed -f "$PACKAGE" 2>&1) || { echo "$result"; exit 1; }
            echo "$result"
            [ "$result" = Success ] || exit 1
            printf '%s\n' "$fingerprint" > "$MODDIR/.compiled"
        fi
        ;;
    restore)
        if [ "$mode" = updated-system ] && mounted "$native_target"; then
            owns_native_mount || { echo 'Refusing to unmount another owner'; exit 1; }
            am force-stop "$PACKAGE"
            umount "$native_target" || umount -l "$native_target"
            [ "$(digest "$native_target")" = "$NATIVE_ORIGINAL" ] || exit 1
        fi
        echo 'Native data-app mount restored. Disable/remove module and reboot to remove system overlay.'
        ;;
    status)
        echo "APK path: $target"
        echo "APK hash: $(digest "$target")"
        echo "Native path: $native_target"
        echo "Native hash: $(digest "$native_target")"
        pm list packages -s | grep -x "package:$PACKAGE"
        ;;
    *) echo 'Use apply, restore or status'; exit 1 ;;
esac
