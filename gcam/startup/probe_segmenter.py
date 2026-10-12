"""Bounded, transient JNI diagnostic for APK 132e1827...; requires Frida server.

Hooks observe only. Detaching removes them. Exploratory instrumentation, not a UI test.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import threading
import time
import zipfile

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--serial', required=True)
p.add_argument('--deps', type=Path, required=True)
p.add_argument('--apk', type=Path, required=True)
p.add_argument('--output', type=Path, required=True)
p.add_argument('--attach-after-launch', action='store_true')
p.add_argument('--script', type=Path, help='Alternative read-only observation script')
a = p.parse_args()
supported = {'132e18273b3aafdb93e851f5db88156bd4f82c5032ad8de6594fa5a49ea6fe89',
             'd4ec771a9114778f1689ee256debf128e824e1e305de499e1580667e65d227d7'}
if hashlib.sha256(a.apk.read_bytes()).hexdigest() not in supported:
    raise RuntimeError('Unsupported APK: native offset is version-specific')
with zipfile.ZipFile(a.apk) as archive:
    if hashlib.sha256(archive.read('lib/arm64-v8a/libgcastartup.so')).hexdigest() != '76966e7c150dfcb2795ea5b2119827a7e90b13d8c03035dbc4de583d9d12eaa6':
        raise RuntimeError('Unexpected native ELF')
sys.path.insert(0, str(a.deps.resolve()))
import frida

adb = ['adb', '-s', a.serial]
subprocess.run(adb + ['get-state'], check=True, timeout=15)
a.output.parent.mkdir(parents=True, exist_ok=True)
subprocess.run(adb + ['forward', 'tcp:27043', 'tcp:27042'], check=True, timeout=15)
device = frida.get_device_manager().add_remote_device('127.0.0.1:27043')
package = 'com.android.MGC_9_7_047'
subprocess.run(adb + ['shell', 'am', 'force-stop', package], check=True, timeout=15)
logfile = a.output.with_suffix('.logcat.txt').open('wb')
logger = subprocess.Popen(adb + ['logcat', '-v', 'threadtime', '-T', '1'], stdout=logfile, stderr=subprocess.DEVNULL)
if a.attach_after_launch:
    subprocess.run(adb + ['shell', 'am', 'start', '-W', '-n', package + '/com.android.camera.CameraLauncher'], check=True, timeout=40)
    pid = int(subprocess.check_output(adb + ['shell', 'pidof', package], timeout=15).strip())
else:
    pid = device.spawn([package])
session = device.attach(pid)
a.output.parent.mkdir(parents=True, exist_ok=True)
with a.output.open('w', encoding='utf-8') as out:
    script = session.create_script((a.script or Path(__file__).with_name('segmenter_cache_probe.js')).read_text())
    def message(m, data):
        out.write(json.dumps(m) + '\n')
        out.flush()
        print(json.dumps(m), flush=True)
    script.on('message', message)
    try:
        script.load()
        if not a.attach_after_launch:
            device.resume(pid)
            subprocess.run(adb + ['shell', 'am', 'start', '-W', '-n', package + '/com.android.camera.CameraLauncher'], check=True, timeout=40)
        time.sleep(16)
    finally:
        done = threading.Event()
        def detach():
            try:
                session.detach()
            finally:
                done.set()
        threading.Thread(target=detach, daemon=True).start()
        if not done.wait(5):
            subprocess.run(adb + ['shell', 'am', 'force-stop', package], check=True, timeout=15)
            if not done.wait(5):
                print('Detach did not complete; app was stopped. Retire this trace.', flush=True)
        logger.terminate()
        logger.wait(timeout=10)
        logfile.close()
        subprocess.run(adb + ['forward', '--remove', 'tcp:27043'], check=True, timeout=15)
