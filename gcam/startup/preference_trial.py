"""Reversible startup investigation for the installed BSG APK (ADB/root only).

Private backups belong under dist/. This is a diagnostic utility, not a UI test.
Only the selected preference is restored; other app preferences are preserved.
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
KEYS = {"gate": "camera.gate_activity_controller_init",
        "demand": "camera.on_demand_ui_wirer",
        "logging": "pref_disable_log_key"}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("action", choices=("apply", "restore", "status"))
    p.add_argument("--serial", required=True)
    p.add_argument("--key", choices=KEYS, required=True)
    p.add_argument("--value", choices=("true", "false", "0", "1"))
    p.add_argument("--backup-dir", type=Path, required=True)
    args = p.parse_args()
    if args.action == "apply" and args.value is None:
        p.error("apply requires --value")
    kind = "string" if args.key == "logging" else "boolean"
    if args.action == "apply" and args.value not in (("0", "1") if kind == "string" else ("true", "false")):
        p.error("Value does not match preference type")
    adb = ["adb", "-s", args.serial]

    def run(*parts):
        return subprocess.check_output(adb + list(parts), timeout=40)

    def root(command):
        return run("shell", "su -c " + shlex.quote(command))

    key = KEYS[args.key]
    if args.action != "status":
        run("shell", "am", "force-stop", PACKAGE)
    data = root("cat " + PREF).replace(b"\r", b"")
    tree = ET.fromstring(data)
    found = [e for e in tree if e.get("name") == key]
    if len(found) > 1 or (found and found[0].tag != kind):
        raise RuntimeError("Unexpected preference type/duplicates")
    if args.action == "status":
        print(json.dumps({key: (found[0].text if kind == "string" else found[0].get("value")) if found else None}))
        return
    args.backup_dir.mkdir(parents=True, exist_ok=True)
    state_path = args.backup_dir / (args.key + "-original.json")
    if args.action == "apply":
        if not state_path.exists():
            backup = args.backup_dir / (args.key + "-before.xml")
            backup.write_bytes(data)
            state_path.write_text(json.dumps({"serial": args.serial, "key": key,
                "original": ET.tostring(found[0], encoding="unicode") if found else None,
                "sha256": hashlib.sha256(data).hexdigest()}, indent=2))
        state = json.loads(state_path.read_text())
        desired = ET.Element(kind, name=key)
        if kind == "string":
            desired.text = args.value
        else:
            desired.set("value", args.value)
    else:
        state = json.loads(state_path.read_text())
        backup = (args.backup_dir / (args.key + "-before.xml")).read_bytes()
        if hashlib.sha256(backup).hexdigest() != state["sha256"]:
            raise RuntimeError("Backup integrity failure")
        desired = ET.fromstring(state["original"]) if state["original"] else None
    if state["serial"] != args.serial or state["key"] != key:
        raise RuntimeError("Backup belongs to a different device/key")
    pattern = (rb'<string\b(?=[^>]*\bname="' + re.escape(key.encode()) + rb'")[^>]*>[^<]*</string>'
               if kind == "string" else
               rb'<boolean\b(?=[^>]*\bname="' + re.escape(key.encode()) + rb'")[^>]*/>')
    updated, count = re.subn(pattern, b"", data)
    if count != len(found) or updated.count(b"</map>") != 1:
        raise RuntimeError("Cannot safely edit this XML layout")
    if desired is not None:
        entry = ET.tostring(desired, encoding="utf-8") + b"\n"
        updated = updated.replace(b"</map>", entry + b"</map>")
    ET.fromstring(updated)
    local = args.backup_dir / (args.key + "-" + args.action + ".xml")
    local.write_bytes(updated)
    temp = "/data/local/tmp/x6810-startup-prefs.xml"
    run("push", str(local), temp)
    try:
        root(f"cat {temp} > {PREF}")
        if root("cat " + PREF).replace(b"\r", b"") != updated:
            raise RuntimeError("Preference readback mismatch")
    except Exception:
        local.write_bytes(data)
        run("push", str(local), temp)
        root(f"cat {temp} > {PREF}")
        if root("cat " + PREF).replace(b"\r", b"") != data:
            raise RuntimeError("Recovery failed; app remains stopped")
        raise
    finally:
        run("shell", "rm", "-f", temp)
    print(f"{args.action}: {key}; readback verified; GCam stopped")


if __name__ == "__main__":
    main()
