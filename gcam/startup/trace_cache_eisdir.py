"""Bounded kernel trace of openat EISDIR and user stacks, restoring trace settings.

No native hooks. Requires an idle tracing facility and disabled raw sys_exit event.
Diagnostic output can include other processes and belongs under private dist/.
"""
import argparse
from pathlib import Path
import shlex
import subprocess

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--serial', required=True)
p.add_argument('--output', type=Path, required=True)
a = p.parse_args()
adb = ['adb','-s',a.serial]
tr = '/sys/kernel/tracing/instances/x6810_cache_diag/'
ev = tr+'events/raw_syscalls/sys_exit/'
def root(cmd):
    return subprocess.check_output(adb+['shell','su','-M','-c',shlex.quote(cmd)],timeout=40)
root('mkdir '+tr.rstrip('/'))
root('echo 0 > '+tr+'tracing_on')
if root('cat '+tr+'tracing_on').strip() != b'0' or root('cat '+ev+'enable').strip() != b'0':
    raise RuntimeError('Tracing busy; refusing to modify it')
old_stack = root('cat '+tr+'options/userstacktrace').strip().decode()
old_filter = root('cat '+ev+'filter').strip().decode()
a.output.mkdir(parents=True,exist_ok=False)
try:
    # AArch64 syscall 56 is openat. Filtering preserves only directory-as-file errors.
    root('echo 0 > '+tr+'trace; echo '+shlex.quote('id == 56 && ret == -21')+' > '+ev+'filter; '
         'echo 1 > '+tr+'options/userstacktrace; echo 1 > '+ev+'enable; echo 1 > '+tr+'tracing_on')
    subprocess.run(['python','scripts/collect_mgc_startup.py','--serial',a.serial,
                    '--label','launch','--output',str(a.output),'--seconds','15','--screenshots='],
                   check=True,timeout=55)
    root('echo 0 > '+tr+'tracing_on')
    (a.output/'eisdir.trace').write_bytes(root('cat '+tr+'trace'))
    pid = subprocess.check_output(adb+['shell','pidof','com.android.MGC_9_7_047'],timeout=15).decode().strip()
    if not pid.isdigit():
        raise RuntimeError('App is no longer running')
    (a.output/'app-maps.txt').write_bytes(root('cat /proc/'+pid+'/maps'))
    (a.output/'app-threads.txt').write_bytes(root('ps -T -p '+pid))
finally:
    root('echo 0 > '+tr+'tracing_on; echo 0 > '+ev+'enable; echo '+old_stack+' > '+tr+'options/userstacktrace; '
         'echo '+shlex.quote('0' if old_filter == 'none' else old_filter)+' > '+ev+'filter')
    root('rmdir '+tr.rstrip('/'))
print('Captured EISDIR diagnostic and restored tracing')
