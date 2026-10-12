"""ABBA logging preference experiment; restores preference and retained APK."""
import argparse
import json
from pathlib import Path
import re
import shlex
import subprocess

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--serial', required=True)
p.add_argument('--output', type=Path, required=True)
p.add_argument('--runs', type=int, default=3, choices=range(1, 6))
a = p.parse_args()
a.output.mkdir(parents=True, exist_ok=False)
apk = Path('dist/analysis/gcam-crc-20261011/crc-diagnostic.apk')
checksum = json.loads(apk.with_suffix('.json').read_text())['trial_sha256']
module = '/data/adb/modules_update/x6810_gcam_startup/activate.sh'
adb = ['adb', '-s', a.serial]
pref = ['python', 'gcam/startup/preference_trial.py']
pref_args = ['--serial', a.serial, '--key', 'logging', '--backup-dir', str(a.output/'prefs')]
mount = ['python', 'gcam/apk-analysis/mount_trial.py', '--serial', a.serial]

def run(cmd):
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    print(result.stdout, flush=True)
    if result.stderr:
        print(result.stderr, flush=True)
    result.check_returncode()
    return result.stdout

def activate(action):
    run(adb+['shell', 'su', '-M', '-c', shlex.quote('/system/bin/sh '+module+' '+action)])

rows = []
mounted = False
try:
    activate('restore')
    mounted = True  # finally also covers a partially successful mount
    run(mount+['apply', '--apk', str(apk), '--expected-trial-hash', checksum])
    if run(adb+['shell', 'cmd', 'package', 'compile', '-m', 'speed', '-f',
                'com.android.MGC_9_7_047']).strip() != 'Success':
        raise RuntimeError('ART compilation failed')
    for group, value in enumerate(('0', '1', '1', '0'), 1):
        run(pref+['apply']+pref_args+['--value', value])
        for iteration in range(a.runs+1):
            label = f'g{group}_logging{value}_'+('warmup' if iteration == 0 else str(iteration))
            run(['python', 'scripts/collect_mgc_startup.py', '--serial', a.serial,
                 '--output', str(a.output/'measurements'), '--label', label,
                 '--seconds', '8', '--screenshots='])
            folder = a.output/'measurements'/label
            logs = (folder/'app-logcat.txt').read_text(errors='replace')
            events = {name: int(ns) for name, ns in re.findall(
                r'X6810_PREVIEW:\s*event=(\w+) raw_ns=(\d+)', logs)}
            if iteration == 0:
                continue
            origin = events['ACTIVITY_ONCREATE_START']
            if 'ACTIVITY_FIRST_PREVIEW_FRAME_RENDERED' not in events:
                raise RuntimeError('Missing preview marker')
            row = dict(label=label, logging_enabled=value == '0',
                       initial_display_ms=json.loads((folder/'summary.json').read_text())['initial_display_ms'],
                       events_ms={k: (v-origin)/1e6 for k,v in events.items()},
                       fatal='FATAL EXCEPTION' in logs or 'ANR in' in logs,
                       cache_error='Failed to updated cache' in logs)
            rows.append(row)
            (a.output/'results.json').write_text(json.dumps(rows, indent=2)+'\n')
            print(json.dumps(row), flush=True)
finally:
    try:
        if (a.output/'prefs/logging-original.json').exists():
            run(pref+['restore']+pref_args)
    finally:
        try:
            if mounted:
                run(mount+['restore', '--expected-trial-hash', checksum])
        finally:
            activate('apply')
