"""Exercise ELF cache reuse and recovery on the explicitly selected rooted device.

Touches only the derived codec_hevc.lck, with a verified same-directory backup.
Never clears app data. Requires the exact CRC trial mount. Restores on failure.
"""
import argparse
import json
from pathlib import Path
import shlex
import subprocess

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--serial', required=True)
p.add_argument('--output', type=Path, required=True)
a = p.parse_args()
trial = 'd4ec771a9114778f1689ee256debf128e824e1e305de499e1580667e65d227d7'
expected = 'fe4494b6fbb4424c302cc53ea387699e4d43dfa9d0ba0d1ac9c3fc952428de90'
pkg = 'com.android.MGC_9_7_047'
target = '/data/user/0/'+pkg+'/cache/codec_hevc.lck'
backup = target+'.x6810_crc_backup'
adb = ['adb', '-s', a.serial]
def run(*args):
    return subprocess.check_output(adb+list(args), timeout=45).decode().strip()
def root(cmd):
    return run('shell','su','-M','-c',shlex.quote(cmd))
apk = run('shell','pm','path',pkg).removeprefix('package:')
if root('sha256sum '+shlex.quote(apk)).split()[0] != trial:
    raise RuntimeError('Expected release CRC trial mount')
if root('sha256sum '+target).split()[0] != expected:
    raise RuntimeError('Initial extracted ELF differs from audited asset')
root('test ! -e '+backup)
a.output.mkdir(parents=True, exist_ok=False)
run('shell','am','force-stop',pkg)
root('cp -p '+target+' '+backup)
if root('sha256sum '+backup).split()[0] != expected:
    raise RuntimeError('Backup verification failed; original untouched')
rows = []
success = False
try:
    for case in ('reuse','missing','bad_header','bad_body','truncated','reuse_after_recovery'):
        run('shell','am','force-stop',pkg)
        before = root('stat -c %s:%Y:%i '+target)
        if case == 'missing':
            root('rm '+target)
        elif case in ('bad_header','bad_body'):
            offset = 0 if case == 'bad_header' else 4
            root(f'dd if=/dev/zero of={target} bs=1 seek={offset} count=1 conv=notrunc')
        elif case == 'truncated':
            root('truncate -s 4096 '+target)
        if case not in ('reuse','reuse_after_recovery'):
            damaged = root('sha256sum '+target+' 2>/dev/null || echo missing').split()[0]
            if damaged == expected:
                raise RuntimeError('Damage was not applied: '+case)
        subprocess.run(['python','scripts/collect_mgc_startup.py','--serial',a.serial,
                        '--label',case,'--output',str(a.output),'--seconds','6',
                        '--screenshots='],check=True,timeout=60)
        after = root('stat -c %s:%Y:%i '+target)
        digest = root('sha256sum '+target).split()[0]
        logs = (a.output/case/'app-logcat.txt').read_text(errors='replace')
        fatal = any(s in logs for s in ('FATAL EXCEPTION','VerifyError','UnsatisfiedLinkError','ANR in','Fatal signal'))
        valid = digest == expected and not fatal
        if case in ('reuse','reuse_after_recovery'):
            valid = valid and before == after
        summary = json.loads((a.output/case/'summary.json').read_text())
        valid = valid and summary['pid'].isdigit()
        rows.append({'case':case,'passed':valid,'before':before,'after':after,
                     'sha256':digest,'fatal':fatal,'ttid_ms':summary['initial_display_ms']})
        (a.output/'results.json').write_text(json.dumps(rows,indent=2)+'\n')
        print(json.dumps(rows[-1]),flush=True)
        if not valid:
            raise RuntimeError('Cache validation failed: '+case)
    success = True
finally:
    if not success:
        run('shell','am','force-stop',pkg)
        root('cp -p '+backup+' '+target)
        if root('sha256sum '+target).split()[0] != expected:
            raise RuntimeError('Backup restoration failed; backup retained at '+backup)
    root('rm '+backup)
