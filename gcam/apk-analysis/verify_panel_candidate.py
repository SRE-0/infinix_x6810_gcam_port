"""Bounded ADB panel diagnostic with fresh UI locators and final mount restoration."""
import argparse
import json
from pathlib import Path
import re
import shlex
import subprocess
import time
import xml.etree.ElementTree as ET

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--serial', required=True)
p.add_argument('--apk', type=Path, required=True)
p.add_argument('--output', type=Path, required=True)
a = p.parse_args()
if a.output.exists():
    raise FileExistsError(a.output)
a.output.mkdir(parents=True)
package = 'com.android.MGC_9_7_047'
adb = ['adb','-s',a.serial]
checksum = json.loads(a.apk.with_suffix('.json').read_text())['trial_sha256']
library = Path('dist/analysis/gcam-next-20261011/libgcastartup-cache.so')
native_hash = json.loads(library.with_suffix('.json').read_text())['trial_sha256']
module = '/data/adb/modules_update/x6810_gcam_startup/activate.sh'
mount = ['python','gcam/apk-analysis/mount_trial.py','--serial',a.serial]
native = ['python','gcam/apk-analysis/mount_native_trial.py','--serial',a.serial]
steps = []
active = native_active = False
logger = None
log = None

def run(cmd, timeout=180):
    r = subprocess.run(cmd,capture_output=True,timeout=timeout)
    r.check_returncode()
    return r.stdout

def shell(*parts):
    return run(adb+['shell']+list(parts),timeout=40)

def activate(action):
    print(run(adb+['shell','su','-M','-c',shlex.quote('/system/bin/sh '+module+' '+action)]).decode(),flush=True)

def ui(label):
    remote = '/sdcard/x6810-panel-verify.xml'
    shell('rm','-f',remote)
    out = shell('uiautomator','dump',remote)
    if b'dumped to:' not in out:
        raise RuntimeError('Fresh hierarchy unavailable')
    xml = shell('cat',remote)
    (a.output/(label+'.xml')).write_bytes(xml)
    return list(ET.fromstring(xml).iter('node'))

def choose(nodes,key,value):
    matches = [n for n in nodes if n.get(key)==value and n.get('package')==package
               and n.get('enabled')=='true' and n.get('clickable')=='true']
    if len(matches)!=1:
        raise RuntimeError(f'Expected unique enabled {key}={value}: {len(matches)}')
    return matches[0]

def tap(label,key,value):
    node = choose(ui(label),key,value)
    x1,y1,x2,y2 = map(int,re.findall(r'\d+',node.get('bounds')))
    shell('input','tap',str((x1+x2)//2),str((y1+y2)//2))
    steps.append(dict(action='tap',label=label,selector={key:value},bounds=node.get('bounds')))

def open_panel(label, focus=True):
    tap(label+'-entry','resource-id',package+':id/options_entry_button')
    nodes = ui(label+'-general')
    required = ['Google AWB options','HDR+ options','Timer options','Ratio']
    if focus:
        required.append('Focus options')
    descriptions = {n.get('content-desc') for n in nodes}
    if not set(required)<=descriptions:
        raise RuntimeError('Missing panel categories: '+str(set(required)-descriptions))
    choose(nodes,'content-desc','Pro')
    shell('screencap','-p','/sdcard/x6810-panel-verify.png')
    run(adb+['pull','/sdcard/x6810-panel-verify.png',str(a.output/(label+'.png'))])
    steps.append(dict(action='panel-visible',label=label,categories=required))

def launch(label):
    shell('am','force-stop',package)
    time.sleep(1)
    shell('log','-t','X6810_STARTUP',label)
    (a.output/(label+'-am.txt')).write_bytes(shell('am','start','-W','-n',package+'/com.android.camera.CameraLauncher'))
    time.sleep(3)

try:
    activate('restore')
    active = True
    run(mount+['apply','--apk',str(a.apk),'--expected-trial-hash',checksum])
    native_active = True
    run(native+['apply','--library',str(library),'--expected-trial-hash',native_hash])
    if shell('cmd','package','compile','-m','speed','-f',package).strip()!=b'Success':
        raise RuntimeError('ART compilation failed')
    log = (a.output/'logcat.txt').open('wb')
    logger = subprocess.Popen(adb+['logcat','-b','main','-b','system','-b','events','-v','threadtime','-T','1'],stdout=log,stderr=subprocess.DEVNULL)
    launch('panel-first-touch')
    open_panel('first-touch')
    tap('pro-tab','content-desc','Pro')
    nodes = ui('pro-visible')
    if not any('RAW' in (n.get('text','')+n.get('content-desc','')) for n in nodes):
        raise RuntimeError('RAW control absent from Pro')
    tap('general-tab','content-desc','General')
    tap('awb-enable','content-desc','Google AWB on')
    try:
        if choose(ui('awb-on'),'content-desc','Google AWB on').get('selected')!='true':
            raise RuntimeError('AWB selection did not update')
    finally:
        tap('awb-restore','content-desc','Google AWB off')
    if choose(ui('awb-off'),'content-desc','Google AWB off').get('selected')!='true':
        raise RuntimeError('AWB restoration not reflected')
    shell('input','keyevent','4')
    open_panel('second-touch')
    shell('input','keyevent','4')
    launch('panel-first-gesture')
    node = choose(ui('gesture-entry'),'resource-id',package+':id/options_entry_button')
    x1,y1,x2,y2 = map(int,re.findall(r'\d+',node.get('bounds')))
    shell('input','swipe',str((x1+x2)//2),str((y1+y2)//2),str((x1+x2)//2),str(y1//2),'400')
    nodes = ui('gesture-open')
    choose(nodes,'content-desc','Pro')
    if not any(n.get('content-desc')=='Google AWB options' for n in nodes):
        raise RuntimeError('Gesture did not populate panel')
    steps.append(dict(action='first-gesture',entry_bounds=node.get('bounds')))
    shell('input','keyevent','4')
    tap('front-switch','content-desc','Switch to front camera')
    time.sleep(2)
    open_panel('front', focus=False)
    shell('input','keyevent','4')
    tap('rear-switch','content-desc','Switch to back camera')
    time.sleep(2)
    tap('tele-switch','text','4.9')
    time.sleep(2)
    open_panel('tele')
    shell('input','keyevent','4')
    tap('main-switch','text','1.0')
    tap('portrait-mode','text','Portrait')
    time.sleep(2)
    # Mode change before opening PHOTO's pending panel must also remain valid.
    tap('photo-mode','text','Photo')
    time.sleep(2)
    shell('input','keyevent','3')
    time.sleep(1)
    shell('am','start','-W','-n',package+'/com.android.camera.CameraLauncher')
    time.sleep(2)
    open_panel('resume')
    shell('input','keyevent','4')
    steps.append(dict(action='resume-and-mode-switches',result='pass'))
    print(json.dumps(steps,indent=2),flush=True)
finally:
    if logger:
        logger.terminate()
        logger.wait(timeout=5)
    if log:
        log.close()
    (a.output/'actions.json').write_text(json.dumps(steps,indent=2)+'\n')
    try:
        if native_active:
            run(native+['restore','--expected-trial-hash',native_hash])
    finally:
        try:
            if active:
                run(mount+['restore','--expected-trial-hash',checksum])
        finally:
            activate('apply')
