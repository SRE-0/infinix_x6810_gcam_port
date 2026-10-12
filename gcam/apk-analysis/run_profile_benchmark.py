"""Run sequential ABBA process-cold launches; always restore the original APK.

Uses existing ADB-verified collectors. Warmup launches are retained but excluded.
Does not clear app data or caches. Baseline/trial have identical event logging.
"""
import argparse
import json
from pathlib import Path
import re
import subprocess

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--serial', required=True)
p.add_argument('--directory', type=Path, required=True)
p.add_argument('--prefix', default='profiles')
p.add_argument('--runs', type=int, default=3, choices=range(1, 6))
p.add_argument('--trial-variant', default='profile-cache', choices=('profile-cache', 'profile-cache-scan6'))
a = p.parse_args()
if not re.fullmatch(r'[A-Za-z0-9_-]+', a.prefix):
    p.error('Invalid prefix')
tool = Path(__file__).parent/'mount_trial.py'
active = None
results = []
def command(args):
    done = subprocess.run(args, text=True, capture_output=True, check=True)
    print(done.stdout, flush=True)
    return done.stdout
def compile_app():
    result = command(['adb', '-s', a.serial, 'shell', 'cmd', 'package', 'compile',
                      '-m', 'speed-profile', '-f', 'com.android.MGC_9_7_047'])
    if result.strip() != 'Success':
        raise RuntimeError('ART compilation did not report Success')
def restore():
    global active
    if active:
        command(['python', str(tool), '--serial', a.serial, 'restore', '--expected-trial-hash', active])
        active = None
def launch(label):
    command(['python', 'scripts/collect_mgc_startup.py', '--serial', a.serial,
             '--label', label, '--output', str(a.directory/'measurements'),
             '--seconds', '7', '--screenshots='])
try:
    for group, variant in enumerate(('baseline', a.trial_variant, a.trial_variant, 'baseline'), 1):
        apk = a.directory/(variant+'.apk')
        checksum = json.loads(apk.with_suffix('.json').read_text())['trial_sha256']
        if active != checksum:
            restore()
            command(['python', str(tool), '--serial', a.serial, 'apply', '--apk', str(apk),
                     '--expected-trial-hash', checksum])
            active = checksum
            compile_app()
        launch(f'{a.prefix}_g{group}_{variant}_warmup')
        for run in range(1, a.runs+1):
            label = f'{a.prefix}_g{group}_{variant}_{run}'
            launch(label)
            out = a.directory/'measurements'/label
            summary = json.loads((out/'summary.json').read_text())
            text = (out/'app-logcat.txt').read_text(errors='replace')
            events = dict((name, int(ns)) for name, ns in
                          re.findall(r'X6810_PREVIEW:\s*event=(\w+) raw_ns=(\d+)', text))
            origin = events.get('ACTIVITY_ONCREATE_START')
            if origin is None or 'ACTIVITY_FIRST_PREVIEW_FRAME_RENDERED' not in events:
                raise RuntimeError('Missing preview timing events: '+label)
            row = {'label': label, 'variant': variant, 'initial_display_ms': summary['initial_display_ms'],
                   'events_ms': {k: round((v-origin)/1e6, 3) for k,v in events.items()},
                   'fatal': 'FATAL EXCEPTION' in text or 'ANR in' in text}
            results.append(row)
            (a.directory/(a.prefix+'-results.json')).write_text(json.dumps(results, indent=2)+'\n')
            print('MEASUREMENT '+json.dumps(row), flush=True)
finally:
    restore()
    compile_app()
