"""One GCam diagnostic tap using a fresh ADB UI hierarchy and verified bounds."""
import argparse
import json
from pathlib import Path
import re
import subprocess
import xml.etree.ElementTree as ET

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--serial', required=True)
p.add_argument('--output', type=Path, required=True)
selector = p.add_mutually_exclusive_group(required=True)
selector.add_argument('--id')
selector.add_argument('--text')
selector.add_argument('--description')
a = p.parse_args()
if a.output.exists():
    raise FileExistsError(a.output)
package = 'com.android.MGC_9_7_047'
adb = ['adb','-s',a.serial]
def run(*parts):
    return subprocess.check_output(adb+list(parts),timeout=35)
remote = '/sdcard/x6810-action-ui.xml'
run('shell','rm','-f',remote)
result = run('shell','uiautomator','dump',remote)
if b'UI hierchary dumped to:' not in result and b'UI hierarchy dumped to:' not in result:
    raise RuntimeError('Fresh UI hierarchy unavailable')
xml = run('shell','cat',remote)
key,value = ('resource-id',package+':id/'+a.id) if a.id else ('text',a.text) if a.text else ('content-desc',a.description)
nodes = [n for n in ET.fromstring(xml).iter('node') if n.get(key)==value and
         n.get('package')==package and n.get('clickable')=='true' and n.get('enabled')=='true']
if len(nodes)!=1:
    raise RuntimeError('Expected one enabled clickable match: '+str(len(nodes)))
coords = [int(x) for x in re.findall(r'\d+',nodes[0].get('bounds',''))]
if len(coords)!=4 or coords[2]<=coords[0] or coords[3]<=coords[1]:
    raise RuntimeError('Invalid UI bounds')
a.output.parent.mkdir(parents=True,exist_ok=True)
a.output.write_bytes(xml)
x,y = (coords[0]+coords[2])//2,(coords[1]+coords[3])//2
run('shell','input','tap',str(x),str(y))
record = dict(selector={key:value},bounds=nodes[0].get('bounds'),tap=[x,y])
a.output.with_suffix('.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(record))
