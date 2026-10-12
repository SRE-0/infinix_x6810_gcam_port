"""Apply small, reversible sensor-specific BSG V18 preference overlays.

No vendor or APatch module writes. Requires an explicit device and local backup.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shlex
import subprocess
import xml.etree.ElementTree as ET

PACKAGE = 'com.android.MGC_9_7_047'
VERSION = '9.7.047.702121536.18'
APK_SHA256 = '132e18273b3aafdb93e851f5db88156bd4f82c5032ad8de6594fa5a49ea6fe89'
PREF = f'/data/user/0/{PACKAGE}/shared_prefs/{PACKAGE}_preferences.xml'
PROFILES = Path(__file__).resolve().parents[1] / 'profiles/gcam-bsg-v18.json'


def overlay(data, changes):
    tree = ET.fromstring(data)
    if tree.tag != 'map':
        raise ValueError('Expected SharedPreferences map')
    for key, desired in changes.items():
        if not re.fullmatch(r'[A-Za-z0-9_.]+', key):
            raise ValueError('Invalid key')
        matches = [e for e in tree if e.get('name') == key]
        if len(matches) > 1 or (matches and matches[0].tag != 'string'):
            raise ValueError(f'Unexpected type/duplicate: {key}')
        pattern = rb'<string\b(?=[^>]*\bname="' + key.encode() + rb'")[^>]*>.*?</string>'
        data, count = re.subn(pattern, b'', data, flags=re.S)
        if count != len(matches):
            raise ValueError('Unsupported XML representation')
        if desired is not None:
            entry = ET.Element('string', name=key)
            entry.text = desired
            serialized = ET.tostring(entry, encoding='utf-8', short_empty_elements=False)
            if data.count(b'</map>') != 1:
                raise ValueError('Unexpected map terminator')
            data = data.replace(b'</map>', b'    ' + serialized + b'\n</map>')
    ET.fromstring(data)
    return data


def load_xml_overlay(path):
    """Read a minimal Android SharedPreferences map of string values."""
    tree = ET.parse(path).getroot()
    if tree.tag != 'map' or not len(tree):
        raise ValueError('Expected a non-empty SharedPreferences map')
    changes = {}
    for entry in tree:
        key = entry.get('name')
        if entry.tag != 'string' or not key or not re.fullmatch(r'[A-Za-z0-9_.]+', key):
            raise ValueError('Only named string preferences are supported')
        if key in changes:
            raise ValueError(f'Duplicate preference: {key}')
        changes[key] = entry.text or ''
    return changes


class Device:
    def __init__(self, serial):
        self.serial = serial

    def adb(self, *args):
        return subprocess.check_output(['adb', '-s', self.serial, *args], timeout=60)

    def root(self, command):
        return self.adb('shell', 'su -c ' + shlex.quote(command))

    def read(self):
        return self.root('cat ' + PREF).replace(b'\r', b'')

    def write(self, data, local):
        local.write_bytes(data)
        remote = '/data/local/tmp/x6810-photo-preferences.xml'
        self.adb('push', str(local), remote)
        try:
            self.root(f'cat {remote} > {PREF}')
            if self.read() != data:
                raise RuntimeError('Preference readback failed')
        finally:
            self.adb('shell', 'rm', '-f', remote)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['apply', 'restore', 'status', 'export'])
    parser.add_argument('--serial', required=True)
    parser.add_argument('--backup-dir', type=Path, required=True)
    parser.add_argument('--sensor', choices=['main', 'tele', 'front', 'rear', 'all'], default='main')
    parser.add_argument('--variant', choices=['standard', 'detail', 'night', 'night-google-awb'], default='standard')
    parser.add_argument('--profile-xml', type=Path,
                        help='Apply a partial SharedPreferences overlay XML instead of the JSON sensor profile')
    args = parser.parse_args()
    if args.profile_xml:
        if not args.profile_xml.is_file():
            parser.error(f'XML overlay not found: {args.profile_xml}')
        changes = load_xml_overlay(args.profile_xml)
        scope = 'xml-overlay'
    else:
        profiles = json.loads(PROFILES.read_text(encoding='utf8'))
        if args.variant.startswith('night') and args.sensor in ('front', 'all'):
            parser.error('Night profiles support main, tele or rear only; frontal excluded')
        selected = (profiles['sensors'] if args.sensor == 'all' else
                    {name: profiles['sensors'][name] for name in ('main', 'tele')} if args.sensor == 'rear' else
                    {args.sensor: profiles['sensors'][args.sensor]})
        changes = {}
        for name, profile in selected.items():
            if args.variant == 'standard':
                preferences = profile['preferences']
            else:
                if args.variant not in profile.get('variants', {}):
                    parser.error(f'{name} has no {args.variant} variant; select a single supported sensor')
                preferences = profile['variants'][args.variant]['preferences']
            changes.update(preferences)
        scope = f'{args.sensor}-{args.variant}'
    device = Device(args.serial)
    if device.adb('get-state').strip() != b'device' or b'uid=0' not in device.root('id'):
        raise RuntimeError('Authorized device and root required')
    package = device.adb('shell', 'dumpsys', 'package', PACKAGE).decode()
    if f'versionName={VERSION}' not in package:
        raise RuntimeError('Only audited BSG V18 is supported')
    data = device.read()
    if args.action == 'status':
        entries = {e.get('name'): e.text for e in ET.fromstring(data)}
        print(json.dumps({k: entries.get(k) for k in changes}, indent=2))
        return
    args.backup_dir.mkdir(parents=True, exist_ok=True)
    if args.action == 'export':
        output = args.backup_dir / ('x6810-' + scope + '.xml')
        output.write_bytes(overlay(data, changes))
        print(output)
        return
    # Verify the APK too: version names alone do not identify port code.
    remote = device.adb('shell', 'pm', 'path', PACKAGE).decode().strip().removeprefix('package:')
    if device.root('sha256sum ' + shlex.quote(remote)).decode().split()[0] != APK_SHA256:
        raise RuntimeError('APK hash differs from audited build')
    device.adb('shell', 'am', 'force-stop', PACKAGE)
    data = device.read()
    state_file = args.backup_dir / 'photo-original.json'
    baseline = args.backup_dir / 'photo-original.xml'
    if not state_file.exists():
        if args.action == 'restore':
            raise RuntimeError('No saved baseline')
        with baseline.open('xb') as stream:
            stream.write(data)
        state_file.write_text(json.dumps({'serial': args.serial, 'package': PACKAGE,
            'sha256': hashlib.sha256(data).hexdigest(), 'original': {
                e.get('name'): e.text or '' for e in ET.fromstring(data) if e.tag == 'string'}}, indent=2), encoding='utf8')
    state = json.loads(state_file.read_text(encoding='utf8'))
    if state['serial'] != args.serial or state['package'] != PACKAGE:
        raise RuntimeError('Backup belongs to another device/package')
    if hashlib.sha256(baseline.read_bytes()).hexdigest() != state['sha256']:
        raise RuntimeError('Backup integrity failed')
    if args.action == 'restore':
        changes = {k: state['original'].get(k) for k in changes}
    updated = overlay(data, changes)
    try:
        device.write(updated, args.backup_dir / ('preferences-' + args.action + '.xml'))
    except Exception:
        device.write(data, args.backup_dir / 'preferences-recovery.xml')
        raise
    print(f'{args.action}: {scope}; readback verified; app stopped')


if __name__ == '__main__':
    main()
