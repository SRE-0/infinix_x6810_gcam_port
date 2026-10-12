#!/system/bin/sh
MODDIR=${0%/*}
attempt=0
while [ "$(getprop sys.boot_completed)" != 1 ]; do
    attempt=$((attempt + 1))
    [ "$attempt" -lt 150 ] || exit 1
    sleep 2
done
[ ! -f "$MODDIR/disable" ] && [ ! -f "$MODDIR/remove" ] || exit 0
# Grants must not depend on ART compilation or a native optimization succeeding.
su -M -c "/system/bin/sh '$MODDIR/permissions.sh'" > "$MODDIR/permissions-status.txt" 2>&1
permission_result=$?
su -M -c "/system/bin/sh '$MODDIR/activate.sh' apply" > "$MODDIR/status.txt" 2>&1
optimization_result=$?
echo "Permissions exit: $permission_result; optimization exit: $optimization_result" >> "$MODDIR/status.txt"
[ "$permission_result" -eq 0 ] && [ "$optimization_result" -eq 0 ]
