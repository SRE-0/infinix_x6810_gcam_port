"""Collect bounded root ftrace alongside a process-cold GCam startup capture."""
import argparse
from pathlib import Path
import shlex
import subprocess

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--serial', required=True)
p.add_argument('--label', required=True)
p.add_argument('--output', type=Path, required=True)
p.add_argument('--seconds', type=int, default=5, choices=range(3, 11))
a = p.parse_args()
adb = ['adb', '-s', a.serial]
out = a.output/a.label
out.mkdir(parents=True, exist_ok=False)

def root(command):
    return subprocess.check_output(adb+['shell', 'su', '-M', '-c', shlex.quote(command)], timeout=35)

if root('cat /sys/kernel/tracing/tracing_on').strip() != b'0':
    raise RuntimeError('Another trace is active; refusing to change it')
flags = root('getprop debug.atrace.tags.enableflags').decode().strip()
buffer = root('cat /sys/kernel/tracing/buffer_size_kb').decode().strip()
try:
    setup = root('atrace --async_start -b 32768 -a com.android.MGC_9_7_047 sched freq idle am wm gfx view camera binder_driver dalvik')
    (out/'atrace-setup.txt').write_bytes(setup)
    # This vendor reports record-tgid failure even with tracing enabled.
    # Accept only a confirmed active trace; do not claim a clean setup.
    if root('cat /sys/kernel/tracing/tracing_on').strip() != b'1':
        raise RuntimeError('atrace did not enable tracing')
    root('echo > /sys/kernel/tracing/trace')
    result = subprocess.run(['python', 'scripts/collect_mgc_startup.py', '--serial', a.serial,
                             '--label', a.label, '--output', str(a.output/'measurements'),
                             '--seconds', str(a.seconds), '--screenshots='], check=False)
    root('echo 0 > /sys/kernel/tracing/tracing_on')
    with (out/'startup.atrace').open('wb') as stream:
        subprocess.run(adb+['shell', '-T', 'su', '-M', '-c', shlex.quote('cat /sys/kernel/tracing/trace')],
                       stdout=stream, check=True, timeout=60)
    with (out/'startup.atrace').open('rb') as stream:
        if not stream.read(128).startswith(b'# tracer:'):
            raise RuntimeError('Invalid trace transfer; inspect the artifact')
    if result.returncode:
        raise RuntimeError('Startup collection failed; inspect artifacts')
finally:
    root('echo 0 > /sys/kernel/tracing/tracing_on')
    root('atrace --async_stop > /dev/null')
    root('setprop debug.atrace.tags.enableflags '+shlex.quote(flags or '0'))
    root('echo '+shlex.quote(buffer)+' > /sys/kernel/tracing/buffer_size_kb')
print(out/'startup.atrace')
