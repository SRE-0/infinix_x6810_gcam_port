"""ABBA native-only experiment with identical Java diagnostics; restore both binds."""
import argparse
import json
from pathlib import Path
import shlex
import subprocess

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--serial', required=True)
p.add_argument('--output', type=Path, required=True)
a = p.parse_args()
if a.output.exists():
    raise FileExistsError(a.output)
directory = Path('dist/analysis/gcam-next-20261011')
apk = directory/'remaining-probe.apk'
library = directory/'libgcastartup-cache.so'
apk_hash = json.loads(apk.with_suffix('.json').read_text())['trial_sha256']
native_hash = json.loads(library.with_suffix('.json').read_text())['trial_sha256']
adb = ['adb','-s',a.serial]
mount = ['python','gcam/apk-analysis/mount_trial.py','--serial',a.serial]
native = ['python','gcam/apk-analysis/mount_native_trial.py','--serial',a.serial]
module = '/data/adb/modules_update/x6810_gcam_startup/activate.sh'

def run(cmd):
    result = subprocess.run(cmd, text=True, capture_output=True, timeout=180)
    print(result.stdout, flush=True)
    if result.stderr:
        print(result.stderr, flush=True)
    result.check_returncode()
    return result.stdout

def activate(action):
    run(adb+['shell','su','-M','-c',shlex.quote('/system/bin/sh '+module+' '+action)])

active = False
mounted = False
try:
    activate('restore')
    mounted = True
    run(mount+['apply','--apk',str(apk),'--expected-trial-hash',apk_hash])
    if run(adb+['shell','cmd','package','compile','-m','speed','-f','com.android.MGC_9_7_047']).strip() != 'Success':
        raise RuntimeError('ART compilation failed')
    for group, trial in enumerate((False,True,True,False),1):
        if active and not trial:
            run(native+['restore','--expected-trial-hash',native_hash])
            active = False
        if trial and not active:
            active = True
            run(native+['apply','--library',str(library),'--expected-trial-hash',native_hash])
        for iteration in range(3):
            label = f'g{group}_'+('patched' if trial else 'original')+'_'+('warmup' if iteration == 0 else str(iteration))
            run(['python','scripts/collect_mgc_startup.py','--serial',a.serial,
                 '--label',label,'--output',str(a.output),'--seconds','12','--screenshots='])
finally:
    try:
        if active:
            run(native+['restore','--expected-trial-hash',native_hash])
    finally:
        try:
            if mounted:
                run(mount+['restore','--expected-trial-hash',apk_hash])
        finally:
            activate('apply')
