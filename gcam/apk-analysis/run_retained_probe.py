"""Run bounded temporary APK diagnostics and restore the current APatch module."""
import argparse
import json
from pathlib import Path
import shlex
import subprocess

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--serial', required=True)
p.add_argument('--apk', type=Path, required=True)
p.add_argument('--output', type=Path, required=True)
p.add_argument('--runs', type=int, default=2, choices=range(1, 5))
p.add_argument('--seconds', type=int, default=15, choices=range(8, 21))
a = p.parse_args()
if a.output.exists():
    raise FileExistsError(a.output)
checksum = json.loads(a.apk.with_suffix('.json').read_text())['trial_sha256']
adb = ['adb','-s',a.serial]
mount = ['python','gcam/apk-analysis/mount_trial.py','--serial',a.serial]
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

mounted = False
try:
    activate('restore')
    mounted = True
    run(mount+['apply','--apk',str(a.apk),'--expected-trial-hash',checksum])
    if run(adb+['shell','cmd','package','compile','-m','speed','-f','com.android.MGC_9_7_047']).strip() != 'Success':
        raise RuntimeError('ART compilation failed')
    for n in range(1,a.runs+1):
        run(['python','scripts/collect_mgc_startup.py','--serial',a.serial,
             '--label','probe_'+str(n),'--output',str(a.output),
             '--seconds',str(a.seconds),'--screenshots='])
finally:
    try:
        if mounted:
            run(mount+['restore','--expected-trial-hash',checksum])
    finally:
        activate('apply')
