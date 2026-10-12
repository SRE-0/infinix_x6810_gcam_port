"""Validate independent GCam sources offline; no mobile actions."""
import ast
import hashlib
import json
import subprocess
import zipfile
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]

def main():
    tracked = subprocess.check_output(['git', '-c', f'safe.directory={ROOT.as_posix()}', '-C', str(ROOT), 'ls-files', '-z']).decode().split('\0')
    forbidden = [name for name in tracked if Path(name).suffix.lower() in {'.smali', '.dex', '.class'} and (ROOT / name).exists()]
    forbidden += [name for name in tracked if any(part in {'apktool', 'decoded', 'jadx'} for part in Path(name).parts) and (ROOT / name).exists()]
    if forbidden:
        raise ValueError(f'Decoded artifacts must stay local: {forbidden}')
    apk = ROOT / 'gcam/apatch-startup/payload/MGC_9.7.047_V32_MGC.apk'
    with apk.open('rb') as stream:
        if hashlib.file_digest(stream, 'sha256').hexdigest() != '132e18273b3aafdb93e851f5db88156bd4f82c5032ad8de6594fa5a49ea6fe89':
            raise ValueError('Retained signed APK checksum mismatch; run git lfs pull')
    notices = ROOT / 'legal/gcam-apk'
    inventory = json.loads((notices / 'manifest.json').read_text())
    with zipfile.ZipFile(apk) as archive:
        for record in inventory['resources']:
            data = (notices / record['file']).read_bytes()
            if data != archive.read(record['apk_resource']) or hashlib.sha256(data).hexdigest() != record['sha256']:
                raise ValueError('APK license resource changed')
            staged = subprocess.check_output(['git', '-c', f'safe.directory={ROOT.as_posix()}', '-C', str(ROOT), 'show', ':legal/gcam-apk/' + record['file']])
            if staged != data:
                raise ValueError('Git changed license-resource bytes; preserve -text attributes and restage exact resources')
    count = 0
    for directory in ('scripts', 'tools', 'gcam'):
        for p in (ROOT / directory).rglob('*.py'):
            ast.parse(p.read_text(encoding='utf-8'), filename=str(p)); count += 1
    module = ROOT / 'gcam/apatch-startup'
    native = module / 'payload/libgcastartup-cache.so'
    with native.open('rb') as source:
        if hashlib.file_digest(source, 'sha256').hexdigest() != '64cfcb3f598cdf3e75875bdd4cb8e8775a6763be15c3d2240d1d7ee0656f053a':
            raise ValueError('Native cache library hash mismatch; run git lfs pull')
    for p in (module / 'system').rglob('*.xml'):
        ET.parse(p)
    overlay = ET.parse(ROOT / 'profiles/x6810-gcam-bsg-v18-recommended.xml').getroot()
    if overlay.tag != 'map' or len(overlay) != 16 or any(p.tag != 'string' for p in overlay):
        raise ValueError('Unexpected V18 overlay')
    profile_path = ROOT / 'profiles/x6810-gcam-bsg-9.7-v32-recommended.xml'
    if hashlib.sha256(profile_path.read_bytes()).hexdigest() != '1b4014581d5bc07b0b3678ba4cea6be7e3bef7cd7f532e51d02e8907aa0ee9f9':
        raise ValueError('Recommended V32 profile changed; review and update its provenance')
    profile = ET.parse(profile_path).getroot()
    if profile.tag != 'map' or len(profile) != 755 or len({p.get('name') for p in profile}) != 755:
        raise ValueError('Unexpected V32 profile structure or duplicate preference names')
    preferences = {p.get('name'): p for p in profile}
    if preferences['camera.ois_forced_photo_mode'].get('value') != 'true':
        raise ValueError('Recommended V32 photo OIS must be enabled')
    metadata = dict(line.split('=', 1) for line in (module / 'module.prop').read_text().splitlines() if '=' in line)
    if metadata['id'] != 'x6810_gcam_startup' or metadata['version'] != '0.7.0':
        raise ValueError('Unexpected module identity')
    print(f'PASS: {count} Python sources, signed APK/native SHA-256, embedded notices, no tracked decoded artifacts, permission XML, historical V18 and recommended V32 profiles. No device validation.')

if __name__ == '__main__':
    main()
