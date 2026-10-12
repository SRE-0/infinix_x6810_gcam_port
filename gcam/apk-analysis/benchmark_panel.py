"""Bounded panel ABBA with corrected native library constant in both variants."""
import argparse
import json
from pathlib import Path
import re
import shlex
import subprocess

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--serial', required=True)
p.add_argument('--directory', type=Path, required=True)
p.add_argument('--prefix', default='panel_abba')
p.add_argument('--runs', type=int, default=2, choices=range(1, 7))
a = p.parse_args()
if not re.fullmatch(r'[A-Za-z0-9_-]+', a.prefix):
    p.error('Invalid prefix')
if (a.directory/(a.prefix+'-results.json')).exists():
    raise FileExistsError('Evidence already exists')
adb = ['adb','-s',a.serial]
module = '/data/adb/modules_update/x6810_gcam_startup/activate.sh'
mount = ['python','gcam/apk-analysis/mount_trial.py','--serial',a.serial]
native = ['python','gcam/apk-analysis/mount_native_trial.py','--serial',a.serial]
library = Path('dist/analysis/gcam-next-20261011/libgcastartup-cache.so')
native_hash = json.loads(library.with_suffix('.json').read_text())['trial_sha256']
active = None
native_active = False
rows = []

def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=240)
    print(r.stdout, flush=True)
    if r.stderr:
        print(r.stderr, flush=True)
    r.check_returncode()
    return r.stdout

def activate(action):
    run(adb+['shell','su','-M','-c',shlex.quote('/system/bin/sh '+module+' '+action)])

try:
    activate('restore')
    native_active = True
    run(native+['apply','--library',str(library),'--expected-trial-hash',native_hash])
    for group, variant in enumerate(('control','trial','trial','control'), 1):
        apk = a.directory/('panel-'+variant+'.apk')
        checksum = json.loads(apk.with_suffix('.json').read_text())['trial_sha256']
        if checksum != active:
            if active:
                run(mount+['restore','--expected-trial-hash',active])
                active = None
            active = checksum
            run(mount+['apply','--apk',str(apk),'--expected-trial-hash',checksum])
            if run(adb+['shell','cmd','package','compile','-m','speed','-f','com.android.MGC_9_7_047']).strip() != 'Success':
                raise RuntimeError('ART compilation failed')
        for n in range(a.runs+1):
            label = f'{a.prefix}_g{group}_{variant}_'+('warmup' if n == 0 else str(n))
            out = a.directory/'measurements'/label
            if out.exists():
                raise FileExistsError(out)
            run(['python','scripts/collect_mgc_startup.py','--serial',a.serial,
                 '--label',label,'--output',str(a.directory/'measurements'),
                 '--seconds','10','--screenshots='])
            logs = (out/'app-logcat.txt').read_text(errors='replace')
            events = {k:int(v) for k,v in re.findall(r'X6810_PREVIEW:\s*event=(\w+) raw_ns=(\d+)',logs)}
            if any(x in logs for x in ('FATAL EXCEPTION','Fatal signal','ANR in')):
                raise RuntimeError('Fatal event: '+label)
            if 'ACTIVITY_FIRST_PREVIEW_FRAME_RENDERED' not in events or 'ACTIVITY_SHUTTER_BUTTON_ENABLED' not in events:
                raise RuntimeError('Missing readiness events: '+label)
            if n == 0:
                continue
            origin = events['ACTIVITY_ONCREATE_START']
            ev = {k:round((v-origin)/1e6,3) for k,v in events.items()}
            rows.append(dict(label=label,variant=variant,
                             initial_display_ms=json.loads((out/'summary.json').read_text())['initial_display_ms'],
                             events_ms=ev,fatal=False))
            (a.directory/(a.prefix+'-results.json')).write_text(json.dumps(rows,indent=2)+'\n')
            print('MEASUREMENT '+json.dumps(rows[-1]),flush=True)
finally:
    try:
        if active:
            run(mount+['restore','--expected-trial-hash',active])
    finally:
        try:
            if native_active:
                run(native+['restore','--expected-trial-hash',native_hash])
        finally:
            activate('apply')
