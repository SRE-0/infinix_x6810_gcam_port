"""Apply/restore a temporary APK bind mount with APatch, preserving disk APK.

Only the hash-guarded GCam package is affected. Does not disable Android package
signature verification, uninstall the app, edit ART artifacts, or install a boot
module. Restore before a package update or reboot.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shlex
import subprocess

PACKAGE = 'com.android.MGC_9_7_047'
ORIGINAL = '132e18273b3aafdb93e851f5db88156bd4f82c5032ad8de6594fa5a49ea6fe89'

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--serial', required=True)
    p.add_argument('action', choices=['apply', 'restore', 'status'])
    p.add_argument('--apk', type=Path)
    p.add_argument('--expected-trial-hash')
    a = p.parse_args()
    adb = ['adb', '-s', a.serial]
    def run(*args):
        return subprocess.check_output(adb + list(args), timeout=120).decode().strip()
    def root(command): return run('shell', 'su', '-M', '-c', shlex.quote(command))
    lines = run('shell', 'pm', 'path', PACKAGE).splitlines()
    if len(lines) != 1: raise RuntimeError('Expected a single base APK')
    target = lines[0].removeprefix('package:')
    if not target.startswith('/data/app/') or not target.endswith('/base.apk') or PACKAGE not in target:
        raise RuntimeError('Unexpected package path')
    qtarget = shlex.quote(target)
    def digest(): return root('sha256sum ' + qtarget).split()[0]
    def mounts():
        return [x for x in root('cat /proc/self/mountinfo').splitlines()
                if x.split()[4] == target]
    before = digest()
    if a.action == 'apply':
        if not a.apk or not a.expected_trial_hash: p.error('apply needs APK and expected hash')
        trial_hash = hashlib.file_digest(a.apk.open('rb'), 'sha256').hexdigest()
        if trial_hash != a.expected_trial_hash: raise RuntimeError('Trial hash mismatch')
        if before != ORIGINAL or mounts(): raise RuntimeError('Original not present or already mounted')
        remote = '/data/local/tmp/x6810-gcam-trial-' + trial_hash[:16] + '.apk'
        run('shell', 'am', 'force-stop', PACKAGE)
        if root('test -f ' + remote + ' && sha256sum ' + remote + ' || echo missing').split()[0] != trial_hash:
            run('push', str(a.apk), remote)
        root('chown system:system ' + remote)
        root('chmod 0644 ' + remote)
        root('chcon u:object_r:apk_data_file:s0 ' + remote)
        if root('sha256sum ' + remote).split()[0] != trial_hash:
            raise RuntimeError('Uploaded hash mismatch')
        root('mount --bind ' + remote + ' ' + qtarget)
        if digest() != trial_hash:
            try:
                root('umount ' + qtarget)
            except subprocess.CalledProcessError:
                # Android's resource readers can keep this APK open after the
                # app stops. Detach only this already hash-verified bind mount.
                root('umount -l ' + qtarget)
            raise RuntimeError('Mount verification failed, restored')
    elif a.action == 'restore':
        if mounts():
            if not a.expected_trial_hash or before != a.expected_trial_hash:
                raise RuntimeError('Unexpected mount; refusing unmount')
            run('shell', 'am', 'force-stop', PACKAGE)
            try:
                root('umount ' + qtarget)
            except subprocess.CalledProcessError:
                root('umount -l ' + qtarget)
        if digest() != ORIGINAL or mounts(): raise RuntimeError('Original restoration failed')
    print(json.dumps({'action': a.action, 'apk_path': target,
                      'sha256_before': before, 'sha256_after': digest(),
                      'mounts': mounts()}, indent=2))

if __name__ == '__main__': main()
