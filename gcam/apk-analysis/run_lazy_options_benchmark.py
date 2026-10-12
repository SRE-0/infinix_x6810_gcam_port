"""Compare lazy rows against cache+scan6, restoring the retained module finally."""
import argparse
import json
from pathlib import Path
import re
import shlex
import subprocess

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--serial', required=True)
p.add_argument('--directory', type=Path, required=True)
p.add_argument('--module-dir', required=True)
p.add_argument('--prefix', default='lazy')
p.add_argument('--runs', type=int, default=2, choices=range(1, 11))
p.add_argument('--trial-variant', choices=('lazy-options', 'lazy-options-v2', 'native-warm', 'elf-crc'), default='lazy-options')
p.add_argument('--baseline-apk', type=Path, help='Explicit retained baseline APK with identical timing hooks')
p.add_argument('--trial-apk', type=Path, help='Explicit isolated trial APK')
p.add_argument('--compile-mode', choices=('speed-profile', 'speed'), default='speed-profile')
p.add_argument('--observe-elf-cache', action='store_true', help='Record derived ELF size, mtime and inode around each measured launch')
p.add_argument('--start-group', type=int, choices=(1, 4), default=1,
               help='Group 4 permits completing a retained control tail after interrupted logging')
a = p.parse_args()
if a.module_dir not in ('/data/adb/modules/x6810_gcam_startup',
                        '/data/adb/modules_update/x6810_gcam_startup'):
    p.error('Unexpected module directory')
if not re.fullmatch(r'[A-Za-z0-9_-]+', a.prefix):
    p.error('Invalid prefix')
tool = Path(__file__).with_name('mount_trial.py')
active = None
rows = []

def command(args):
    result = subprocess.run(args, text=True, capture_output=True)
    print(result.stdout, flush=True)
    if result.stderr:
        print(result.stderr, flush=True)
    result.check_returncode()
    return result.stdout

def module(action):
    return command(['adb', '-s', a.serial, 'shell', 'su', '-M', '-c',
                    shlex.quote('/system/bin/sh '+a.module_dir+'/activate.sh '+action)])

def compile_app():
    result = command(['adb', '-s', a.serial, 'shell', 'cmd', 'package', 'compile',
                      '-m', a.compile_mode, '-f', 'com.android.MGC_9_7_047'])
    if result.strip() != 'Success':
        raise RuntimeError('Compilation failed')

def restore_trial():
    global active
    if active:
        command(['python', str(tool), '--serial', a.serial, 'restore',
                 '--expected-trial-hash', active])
        active = None

def launch(label):
    command(['python', 'scripts/collect_mgc_startup.py', '--serial', a.serial,
             '--label', label, '--output', str(a.directory/'measurements'),
             '--seconds', '7', '--screenshots='])

def cache_stat():
    return command(['adb','-s',a.serial,'shell','su','-M','-c',shlex.quote(
        'stat -c %s:%Y:%i /data/user/0/com.android.MGC_9_7_047/cache/codec_hevc.lck')]).strip()

module('restore')
try:
    for group, variant in enumerate(('baseline', a.trial_variant, a.trial_variant, 'baseline'), 1):
        if group < a.start_group:
            continue
        apk = ((a.baseline_apk if variant == 'baseline' else a.trial_apk)
               or a.directory/(variant+'.apk'))
        checksum = json.loads(apk.with_suffix('.json').read_text())['trial_sha256']
        if active != checksum:
            restore_trial()
            # Track expected mount before the tool call so finally can restore
            # even if activation is interrupted after mounting.
            active = checksum
            command(['python', str(tool), '--serial', a.serial, 'apply', '--apk', str(apk),
                     '--expected-trial-hash', checksum])
            compile_app()
        launch(f'{a.prefix}_g{group}_{variant}_warmup')
        for run in range(1, a.runs+1):
            label = f'{a.prefix}_g{group}_{variant}_{run}'
            before = cache_stat() if a.observe_elf_cache else None
            launch(label)
            after = cache_stat() if a.observe_elf_cache else None
            out = a.directory/'measurements'/label
            summary = json.loads((out/'summary.json').read_text())
            logs = (out/'app-logcat.txt').read_text(errors='replace')
            events = dict((name, int(ns)) for name, ns in
                          re.findall(r'X6810_PREVIEW:\s*event=(\w+) raw_ns=(\d+)', logs))
            origin = events.get('ACTIVITY_ONCREATE_START')
            if origin is None or 'ACTIVITY_FIRST_PREVIEW_FRAME_RENDERED' not in events:
                raise RuntimeError('Missing preview timing: '+label)
            row = {'label': label, 'variant': variant,
                   'compile_mode': a.compile_mode,
                   'initial_display_ms': summary['initial_display_ms'],
                   'events_ms': {k: round((v-origin)/1e6, 3) for k, v in events.items()},
                   'fatal': 'FATAL EXCEPTION' in logs or 'ANR in' in logs}
            if a.observe_elf_cache:
                row.update(elf_cache_before=before, elf_cache_after=after,
                           elf_cache_rewritten=before != after)
            rows.append(row)
            (a.directory/(a.prefix+'-results.json')).write_text(json.dumps(rows, indent=2)+'\n')
            print('MEASUREMENT '+json.dumps(row), flush=True)
finally:
    try:
        restore_trial()
    finally:
        module('apply')
