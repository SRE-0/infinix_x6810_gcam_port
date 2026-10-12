"""Measure a cold launch followed by a timed shutter input and JPEG creation.

Uses a shutter resource ID from the live UI before launch. This is a functional
probe, not an exact measurement of first-preview/TTFD: input can queue while the
main thread is busy and file creation includes image processing.
"""
import argparse
import json
from pathlib import Path
import re
import subprocess
import time
import xml.etree.ElementTree as ET

PACKAGE = 'com.android.MGC_9_7_047'

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--serial', required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--tap-after', type=float, default=3.0)
    p.add_argument('--warm', action='store_true', help='Capture current verified camera/mode without relaunching')
    a = p.parse_args()
    a.output.mkdir(parents=True, exist_ok=False)
    adb = ['adb', '-s', a.serial]
    def run(*parts): return subprocess.check_output(adb + list(parts), timeout=35)
    def photos():
        return {x for x in run('shell', 'find', '/sdcard/DCIM', '-type', 'f').decode().splitlines()
                if Path(x).name.startswith('PXL_') and x.lower().endswith('.jpg')}
    run('shell', 'rm', '-f', '/sdcard/x6810-trial-ui.xml')
    dumped = run('shell', 'uiautomator', 'dump', '/sdcard/x6810-trial-ui.xml')
    if b'UI hierchary dumped to:' not in dumped and b'UI hierarchy dumped to:' not in dumped:
        raise RuntimeError('Fresh UI hierarchy unavailable; refusing stale shutter bounds')
    xml = run('shell', 'cat', '/sdcard/x6810-trial-ui.xml')
    (a.output/'ui-before.xml').write_bytes(xml)
    nodes = [n for n in ET.fromstring(xml).iter('node')
             if n.get('resource-id') == PACKAGE + ':id/shutter_button' and n.get('enabled') == 'true']
    if len(nodes) != 1: raise RuntimeError('Expected an enabled, uniquely identified shutter')
    coords = [int(x) for x in re.findall(r'\d+', nodes[0].get('bounds'))]
    x, y = (coords[0]+coords[2])//2, (coords[1]+coords[3])//2
    before = photos()
    if not a.warm:
        run('shell', 'am', 'force-stop', PACKAGE)
        time.sleep(2)
    with (a.output/'logcat.txt').open('wb') as log:
        logger = subprocess.Popen(adb + ['logcat', '-b', 'main', '-b', 'system', '-b', 'events',
                                         '-v', 'threadtime', '-T', '1'], stdout=log, stderr=subprocess.DEVNULL)
        launch = None
        try:
            start = time.monotonic()
            if not a.warm:
                launch = subprocess.Popen(adb + ['shell', 'am', 'start', '-W', '-n',
                    PACKAGE + '/com.android.camera.CameraLauncher'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            time.sleep(max(0, start + a.tap_after - time.monotonic()))
            tap_start = time.monotonic() - start
            run('shell', 'input', 'tap', str(x), str(y))
            tap_end = time.monotonic() - start
            new = set()
            while time.monotonic() - start < 20:
                new = photos() - before
                if new: break
                time.sleep(0.5)
            observed = time.monotonic() - start
            stdout, stderr = launch.communicate(timeout=20) if launch else (b'Warm capture: no launch\n', b'')
            (a.output/'am-start.txt').write_bytes(stdout)
            (a.output/'am-start-stderr.txt').write_bytes(stderr)
            for photo in new:
                run('pull', photo, str(a.output/Path(photo).name))
            result = {'warm_capture': a.warm, 'tap_requested_seconds': a.tap_after, 'tap_start_seconds': tap_start,
                      'tap_end_seconds': tap_end, 'shutter_bounds': nodes[0].get('bounds'),
                      'new_files': sorted(new), 'first_file_observed_seconds': observed if new else None,
                      'limitation': 'Input may queue; JPEG creation includes processing. Not TTFD.'}
            (a.output/'result.json').write_text(json.dumps(result, indent=2))
            print(json.dumps(result))
        finally:
            if launch and launch.poll() is None: launch.terminate(); launch.wait(timeout=5)
            logger.terminate(); logger.wait(timeout=5)

if __name__ == '__main__': main()
