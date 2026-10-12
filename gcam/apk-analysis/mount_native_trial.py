"""Hash-guarded reversible bind of only GCam's installed native library."""
import argparse
import hashlib
from pathlib import Path
import shlex
import subprocess

PACKAGE = 'com.android.MGC_9_7_047'
BASELINE = '76966e7c150dfcb2795ea5b2119827a7e90b13d8c03035dbc4de583d9d12eaa6'
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--serial', required=True)
p.add_argument('action', choices=('apply','restore','status'))
p.add_argument('--library', type=Path)
p.add_argument('--expected-trial-hash')
a = p.parse_args()
adb = ['adb','-s',a.serial]
def run(*parts):
    return subprocess.check_output(adb+list(parts), timeout=120).decode().strip()
def root(cmd):
    return run('shell','su','-M','-c',shlex.quote(cmd))
paths = run('shell','pm','path',PACKAGE).splitlines()
if len(paths) != 1:
    raise RuntimeError('Expected one installed APK')
apk = paths[0].removeprefix('package:')
if not apk.startswith('/data/app/') or not apk.endswith('/base.apk') or PACKAGE not in apk:
    raise RuntimeError('Unexpected package path')
target = apk.removesuffix('/base.apk')+'/lib/arm64/libgcastartup.so'
qtarget = shlex.quote(target)
def digest():
    return root('sha256sum '+qtarget).split()[0]
def mounts():
    return [line for line in root('cat /proc/self/mountinfo').splitlines()
            if line.split()[4] == target]
before = digest()
if a.action == 'status':
    print('Native hash:',before,'; mounts:',len(mounts()))
elif a.action == 'apply':
    if not a.library or not a.expected_trial_hash:
        p.error('apply requires library and expected hash')
    if hashlib.file_digest(a.library.open('rb'),'sha256').hexdigest() != a.expected_trial_hash:
        raise RuntimeError('Local trial hash mismatch')
    if before != BASELINE or mounts():
        raise RuntimeError('Original library absent or already mounted')
    remote = '/data/local/tmp/x6810-native-'+a.expected_trial_hash[:16]+'.so'
    run('shell','am','force-stop',PACKAGE)
    if root('test -f '+remote+' && sha256sum '+remote+' || echo missing').split()[0] != a.expected_trial_hash:
        run('push',str(a.library),remote)
    root('chown system:system '+remote)
    root('chmod 0755 '+remote)
    root('chcon u:object_r:apk_data_file:s0 '+remote)
    if root('sha256sum '+remote).split()[0] != a.expected_trial_hash:
        raise RuntimeError('Uploaded native hash mismatch')
    root('mount --bind '+remote+' '+qtarget)
    if digest() != a.expected_trial_hash:
        root('umount -l '+qtarget)
        raise RuntimeError('Native verification failed; restored')
    print('Native trial mounted:',a.expected_trial_hash)
else:
    if mounts():
        if not a.expected_trial_hash or before != a.expected_trial_hash:
            raise RuntimeError('Unexpected library owner; refusing unmount')
        remote = '/data/local/tmp/x6810-native-'+a.expected_trial_hash[:16]+'.so'
        if root('stat -c %d:%i '+qtarget) != root('stat -c %d:%i '+remote):
            raise RuntimeError('Same hash but different mount owner; refusing unmount')
        run('shell','am','force-stop',PACKAGE)
        root('umount -l '+qtarget)
    if digest() != BASELINE or mounts():
        raise RuntimeError('Native restore failed')
    print('Original native library restored:',BASELINE)
