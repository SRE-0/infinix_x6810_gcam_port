#!/system/bin/sh
MODDIR=${0%/*}
/system/bin/su -M -c "/system/bin/sh '$MODDIR/activate.sh' restore" > "$MODDIR/status.txt" 2>&1
