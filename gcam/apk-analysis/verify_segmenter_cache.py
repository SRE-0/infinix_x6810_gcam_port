"""Verify missing/truncated derived GPU cache recovery, then restore all state.

Touches only the exact derived segmenter file, after an intact byte-for-byte
backup. No app data reset, model mutation, reboot, generic cache cleanup or hooks.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shlex
import subprocess

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--serial', required=True)
p.add_argument('--output', type=Path, required=True)
a = p.parse_args()
a.output.mkdir(parents=True, exist_ok=False)
base = Path('dist/analysis/gcam-next-20261011')
apk = base/'remaining-probe.apk'
library = base/'libgcastartup-cache.so'
apk_hash = json.loads(apk.with_suffix('.json').read_text())['trial_sha256']
native_hash = json.loads(library.with_suffix('.json').read_text())['trial_sha256']
package = 'com.android.MGC_9_7_047'
cache = '/storage/emulated/0/Android/data/'+package+'/cache/tflite_vakunov_multi-subject_2018-06-09.fb.enc.cache'
backup = '/data/local/tmp/x6810-segmenter-cache-backup.bin'
adb = ['adb','-s',a.serial]
mount = ['python','gcam/apk-analysis/mount_trial.py','--serial',a.serial]
native = ['python','gcam/apk-analysis/mount_native_trial.py','--serial',a.serial]
module = '/data/adb/modules_update/x6810_gcam_startup/activate.sh'

def run(cmd):
    result = subprocess.run(cmd, text=True, capture_output=True, timeout=180)
    print(result.stdout,flush=True)
    if result.stderr:
        print(result.stderr,flush=True)
    result.check_returncode()
    return result.stdout

def root(cmd):
    # adb shell joins/quotes arguments; -T keeps binary output out of a PTY.
    return subprocess.check_output(adb+['shell','-T','su','-M','-c',shlex.quote(cmd)],timeout=40)

def activate(action):
    run(adb+['shell','su','-M','-c',shlex.quote('/system/bin/sh '+module+' '+action)])

original = root('cat '+cache)
if len(original) < 1024 or original[4:8] != b'AFCM':
    raise RuntimeError('Expected the known generated GPU cache format')
original_hash = hashlib.sha256(original).hexdigest()
(a.output/'cache-before.bin').write_bytes(original)
if root('test -e '+backup+' && echo exists || echo absent').strip() != b'absent':
    raise RuntimeError('Backup path already exists; refusing overwrite')
mounted = False
native_active = False
saved = False
results = []
try:
    activate('restore')
    root('cp '+cache+' '+backup)
    saved = True
    if hashlib.sha256(root('cat '+backup)).hexdigest() != original_hash:
        raise RuntimeError('Backup mismatch')
    mounted = True
    run(mount+['apply','--apk',str(apk),'--expected-trial-hash',apk_hash])
    native_active = True
    run(native+['apply','--library',str(library),'--expected-trial-hash',native_hash])
    if run(adb+['shell','cmd','package','compile','-m','speed','-f',package]).strip() != 'Success':
        raise RuntimeError('ART compilation failed')
    for label in ('missing','reuse_after_missing','truncated','reuse_after_truncated'):
        run(adb+['shell','am','force-stop',package])
        if label == 'missing':
            root('rm '+cache)
        elif label == 'truncated':
            root("printf 'X6810-bad-cache' > "+cache)
        run(['python','scripts/collect_mgc_startup.py','--serial',a.serial,
             '--label',label,'--output',str(a.output/'measurements'),
             '--seconds','12','--screenshots='])
        folder = a.output/'measurements'/label
        logs = (folder/'app-logcat.txt').read_text(errors='replace')
        after = root('cat '+cache)
        (a.output/(label+'-cache.bin')).write_bytes(after)
        stamps = {phase:int(ns) for phase,ns in re.findall(
            r'X6810_REMAINING:\s*site=189 phase=(begin|end) now_ns=(\d+)',logs)}
        valid = len(after)>1024 and after[4:8] == b'AFCM'
        fatal = any(s in logs for s in ('FATAL EXCEPTION','Fatal signal','ANR in'))
        row = dict(label=label, bytes=len(after), gpu_cache_valid=valid,
                   cache_write_error='Failed to updated cache' in logs,
                   inference_error='Could not initialize inference engine' in logs,
                   fatal=fatal, init_ms=(stamps['end']-stamps['begin'])/1e6 if len(stamps)==2 else None,
                   sha256=hashlib.sha256(after).hexdigest())
        results.append(row)
        (a.output/'results.json').write_text(json.dumps(results,indent=2)+'\n')
        print(json.dumps(row),flush=True)
        if not valid or fatal or row['cache_write_error'] or row['inference_error'] or row['init_ms'] is None:
            raise RuntimeError('Recovery failed: '+label)
finally:
    try:
        run(adb+['shell','am','force-stop',package])
        if saved:
            root('cat '+backup+' > '+cache)
            if hashlib.sha256(root('cat '+cache)).hexdigest() != original_hash:
                raise RuntimeError('Original derived cache restoration failed; backup retained')
            root('rm '+backup)
    finally:
        try:
            if native_active:
                run(native+['restore','--expected-trial-hash',native_hash])
        finally:
            try:
                if mounted:
                    run(mount+['restore','--expected-trial-hash',apk_hash])
            finally:
                activate('apply')
print('Recovery cases passed; original derived cache and retained APK restored')
