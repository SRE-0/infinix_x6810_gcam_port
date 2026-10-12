"""Reversible single-app preference experiment. Keeps an exact local baseline."""
import argparse
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'dist/analysis/session-20260923'
PACKAGE = 'com.android.MGC_9_7_047'
PREF = f'/data/user/0/{PACKAGE}/shared_prefs/{PACKAGE}_preferences.xml'

def adb(*args):
    return subprocess.check_output(['adb', *args])

def main():
    p = argparse.ArgumentParser()
    p.add_argument('action', choices=['full-surfaces', 'medium-resolution', 'front-1080', 'restore'])
    args = p.parse_args()
    adb('shell', 'am', 'force-stop', PACKAGE)
    baseline = OUT / 'mgc-prefs-before-experiment.xml'
    if not baseline.exists():
        baseline.write_bytes(adb('shell', f'su -c cat {PREF}'))
    data = baseline.read_bytes()
    if args.action == 'full-surfaces':
        data, count = re.subn(rb'(<string name="surfase_list_key_1">)[^<]*(</string>)',
                             rb'\g<1>1\g<2>', data)
        assert count == 1
    if args.action == 'medium-resolution':
        data, count = re.subn(rb'(<string name="pref_camera_resolution">)[^<]*(</string>)',
                             rb'\g<1>medium\g<2>', data)
        assert count == 1
    if args.action == 'front-1080':
        data, count = re.subn(rb'(<string name="pref_camera_picturesize_front_key">)[^<]*(</string>)',
                             rb'\g<1>1920x1080\g<2>', data)
        assert count == 1
    local = OUT / f'mgc-prefs-{args.action}.xml'
    local.write_bytes(data)
    adb('push', str(local), '/data/local/tmp/x6810-mgc-prefs.xml')
    adb('shell', f"su -c 'cat /data/local/tmp/x6810-mgc-prefs.xml > {PREF}'")
    assert adb('shell', f'su -c cat {PREF}').replace(b'\r', b'') == data.replace(b'\r', b'')
    print(args.action, 'verified; app is stopped')

if __name__ == '__main__':
    main()
