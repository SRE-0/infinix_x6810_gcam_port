"""Inspect live ADB UI, or tap one uniquely identified enabled control.

Diagnostic helper for paths verified on the connected device. No assumed
coordinates: tap bounds are read from the current UIAutomator hierarchy.
"""
import argparse
import json
from pathlib import Path
import re
import subprocess
import xml.etree.ElementTree as ET

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--serial', required=True)
p.add_argument('--output', type=Path, required=True)
p.add_argument('--tap-id')
p.add_argument('--tap-description')
a = p.parse_args()
if a.tap_id and a.tap_description:
    p.error('Select only one locator')
adb = ['adb', '-s', a.serial]
def run(*parts):
    return subprocess.check_output(adb+list(parts), timeout=35)
a.output.parent.mkdir(parents=True, exist_ok=True)
run('shell', 'rm', '-f', '/sdcard/x6810-profile-ui.xml')
dump = run('shell', 'uiautomator', 'dump', '/sdcard/x6810-profile-ui.xml')
if b'UI hierchary dumped to:' not in dump and b'UI hierarchy dumped to:' not in dump:
    raise RuntimeError('Fresh UI hierarchy unavailable; refuse stale controls')
data = run('shell', 'cat', '/sdcard/x6810-profile-ui.xml')
a.output.write_bytes(data)
nodes = list(ET.fromstring(data).iter('node'))
print(json.dumps([dict(n.attrib) for n in nodes if n.get('clickable')=='true'], indent=2))
if a.tap_id or a.tap_description:
    chosen = [n for n in nodes if n.get('enabled')=='true' and n.get('clickable')=='true'
              and (n.get('resource-id')==a.tap_id if a.tap_id else n.get('content-desc')==a.tap_description)]
    if len(chosen)!=1:
        raise RuntimeError('Expected exactly one enabled clickable control')
    x1,y1,x2,y2 = map(int, re.findall(r'\d+', chosen[0].get('bounds')))
    run('shell', 'input', 'tap', str((x1+x2)//2), str((y1+y2)//2))
    print('Tapped live bounds:', chosen[0].get('bounds'))
