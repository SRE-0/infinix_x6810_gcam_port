"""Reversible BSG 9.7 AVC compatibility override; does not modify the camera HAL.

Requires an explicitly selected, authorized ADB device and root. Backups contain
private app settings: keep --backup-dir outside the public source tree.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shlex
import subprocess
import xml.etree.ElementTree as ET

PACKAGE = "com.android.MGC_9_7_047"
PREF = f"/data/user/0/{PACKAGE}/shared_prefs/{PACKAGE}_preferences.xml"
KEY = "avc_profile_high_supported"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("apply", "restore", "status"))
    parser.add_argument("--serial", required=True)
    parser.add_argument("--backup-dir", type=Path, required=True)
    args = parser.parse_args()
    adb = ["adb", "-s", args.serial]

    def run(*parts):
        return subprocess.check_output(adb + list(parts), timeout=30)

    def root(command):
        return run("shell", "su -c " + shlex.quote(command))

    def read():
        data = root("cat " + PREF).replace(b"\r", b"")
        tree = ET.fromstring(data)
        matches = [e for e in tree if e.get("name") == KEY]
        if len(matches) > 1 or (matches and matches[0].tag != "boolean"):
            raise RuntimeError("Unexpected preference type or duplicate key")
        return data, matches[0].get("value") if matches else None

    if args.action == "status":
        _, value = read()
        print(json.dumps({KEY: value, "absent_means": "app/device default"}))
        return
    if run("get-state").strip() != b"device":
        raise RuntimeError("Device is not ready")
    if b"uid=0" not in root("id"):
        raise RuntimeError("Root is required")
    run("shell", "am", "force-stop", PACKAGE)
    data, value = read()
    args.backup_dir.mkdir(parents=True, exist_ok=True)
    state_file = args.backup_dir / "topshot-original.json"
    if args.action == "apply":
        if state_file.exists():
            state = json.loads(state_file.read_text())
            if state["serial"] != args.serial or state["package"] != PACKAGE:
                raise RuntimeError("Backup belongs to another device")
        else:
            backup = args.backup_dir / "preferences-before.xml"
            with backup.open("xb") as stream:
                stream.write(data)
            state = {"serial": args.serial, "package": PACKAGE,
                     "original_value": value,
                     "backup_sha256": hashlib.sha256(data).hexdigest()}
            state_file.write_text(json.dumps(state, indent=2) + "\n")
        desired = "false"
    else:
        state = json.loads(state_file.read_text())
        if state["serial"] != args.serial or state["package"] != PACKAGE:
            raise RuntimeError("Backup belongs to another device/package")
        original = (args.backup_dir / "preferences-before.xml").read_bytes()
        if hashlib.sha256(original).hexdigest() != state["backup_sha256"]:
            raise RuntimeError("Backup integrity check failed")
        desired = state["original_value"]
    pattern = rb'<boolean\b(?=[^>]*\bname="' + KEY.encode() + rb'")[^>]*/>'
    updated, count = re.subn(pattern, b"", data)
    if count != (value is not None):
        raise RuntimeError("Preference could not be safely edited")
    if desired is not None:
        if desired not in ("true", "false"):
            raise RuntimeError("Invalid saved boolean")
        entry = f'    <boolean name="{KEY}" value="{desired}" />\n'.encode()
        if updated.count(b"</map>") != 1:
            raise RuntimeError("Unexpected XML root")
        updated = updated.replace(b"</map>", entry + b"</map>")
    ET.fromstring(updated)
    local = args.backup_dir / f"preferences-{args.action}.xml"
    local.write_bytes(updated)
    temp = "/data/local/tmp/x6810-topshot-preferences.xml"
    run("push", str(local), temp)
    try:
        # Overwrite the existing inode to preserve owner, mode and SELinux label.
        root(f"cat {temp} > {PREF}")
        actual, actual_value = read()
        if actual != updated or actual_value != desired:
            raise RuntimeError("Readback verification failed; app left stopped")
    except Exception:
        recovery = args.backup_dir / "preferences-interrupted-operation.xml"
        recovery.write_bytes(data)
        run("push", str(recovery), temp)
        root(f"cat {temp} > {PREF}")
        if read()[0] != data:
            raise RuntimeError("Recovery verification failed; use saved backup")
        raise
    finally:
        run("shell", "rm", "-f", temp)
    print(f"{args.action}: {KEY}={desired}; readback verified; app left stopped")


if __name__ == "__main__":
    main()
