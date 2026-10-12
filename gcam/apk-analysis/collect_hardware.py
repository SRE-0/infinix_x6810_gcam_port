"""Read connected X6810 hardware, codec configuration and loaded GCam libraries.

Does not change app preferences, properties, thermal policy or camera modules.
Private device output belongs under dist/. Run after selecting the ADB serial.
"""
import argparse
import json
from pathlib import Path
import re
import shlex
import subprocess

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--serial', required=True)
p.add_argument('--output', type=Path, required=True)
a = p.parse_args()
a.output.mkdir(parents=True, exist_ok=False)
adb = ['adb', '-s', a.serial]

commands = {
    'platform': 'getprop ro.hardware; getprop ro.board.platform; getprop ro.soc.model; cat /proc/cpuinfo',
    'gpu': 'dumpsys SurfaceFlinger | grep -i GLES; ls -l /vendor/lib64/libOpenCL.so /vendor/lib64/libGLES_mali.so /dev/mali0',
    'codecs': 'find /vendor/etc /odm/etc /system/etc -name "media_codecs*.xml" -type f',
    'neural_services': 'service list | grep -i neural; ls /vendor/lib64 | grep -i -e neuron -e apu -e opencl -e neural',
    'art': 'dumpsys package com.android.MGC_9_7_047',
    'thermal': 'dumpsys thermalservice',
    'library_override': 'ls -l /data/user/0/com.android.MGC_9_7_047/libgcastartup.so',
    'cpu_policy': 'cat /sys/devices/system/cpu/cpufreq/policy*/cpuinfo_max_freq',
}
results = {}
for name, cmd in commands.items():
    r = subprocess.run(adb+['shell', 'su', '-M', '-c', shlex.quote(cmd)],
                       capture_output=True, timeout=40)
    (a.output/(name+'.txt')).write_bytes(r.stdout+r.stderr)
    results[name] = r.returncode
codec_paths = (a.output/'codecs.txt').read_text(errors='replace').splitlines()
for i, path in enumerate(codec_paths):
    if re.fullmatch(r'/(?:vendor|odm|system)/etc/[\w/.-]+\.xml', path.strip()):
        subprocess.run(adb+['pull', path.strip(), str(a.output/f'codec-{i}-{Path(path).name}')],
                       capture_output=True, check=True, timeout=35)
pid = subprocess.check_output(adb+['shell', 'pidof', 'com.android.MGC_9_7_047'],
                              timeout=15).decode().strip()
if re.fullmatch(r'\d+', pid):
    cmd = f'cat /proc/{pid}/maps; ps -T -p {pid}'
    r = subprocess.run(adb+['shell','su','-M','-c',shlex.quote(cmd)],
                       capture_output=True, timeout=35)
    (a.output/'runtime-maps-threads.txt').write_bytes(r.stdout+r.stderr)
(a.output/'results.json').write_text(json.dumps(results, indent=2)+'\n')
print(json.dumps(results))
