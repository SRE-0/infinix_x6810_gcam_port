"""Bounded native cache experiment, restoring native bind and APK afterwards."""
import argparse
import json
from pathlib import Path
import shlex
import subprocess

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--serial', required=True)
p.add_argument('--output', type=Path, required=True)
a = p.parse_args()
library = Path('dist/analysis/gcam-next-20261011/libgcastartup-cache.so')
checksum = json.loads(library.with_suffix('.json').read_text())['trial_sha256']
apk = library.with_name('remaining-probe.apk')
apk_hash = json.loads(apk.with_suffix('.json').read_text())['trial_sha256']
adb = ['adb','-s',a.serial]
native = ['python','gcam/apk-analysis/mount_native_trial.py','--serial',a.serial]
mount = ['python','gcam/apk-analysis/mount_trial.py','--serial',a.serial]
module = '/data/adb/modules_update/x6810_gcam_startup/activate.sh'
def run(cmd):
    subprocess.run(cmd, check=True, timeout=180)
def activate(action):
    run(adb+['shell','su','-M','-c',shlex.quote('/system/bin/sh '+module+' '+action)])
active = False
mounted = False
try:
    activate('restore')
    mounted = True
    run(mount+['apply','--apk',str(apk),'--expected-trial-hash',apk_hash])
    active = True
    run(native+['apply','--library',str(library),'--expected-trial-hash',checksum])
    run(adb+['shell','cmd','package','compile','-m','speed','-f','com.android.MGC_9_7_047'])
    for n in range(1,4):
        run(['python','scripts/collect_mgc_startup.py','--serial',a.serial,
             '--label','probe_'+str(n),'--output',str(a.output),
             '--seconds','15','--screenshots='])
finally:
    try:
        if active:
            run(native+['restore','--expected-trial-hash',checksum])
    finally:
        try:
            if mounted:
                run(mount+['restore','--expected-trial-hash',apk_hash])
        finally:
            activate('apply')
