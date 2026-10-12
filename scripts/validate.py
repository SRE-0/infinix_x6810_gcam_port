"""Validate independent GCam sources offline; no mobile actions."""
import ast
import hashlib
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]

def main():
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
    print(f'PASS: {count} Python sources, native SHA-256, permission XML, historical V18 and recommended V32 profiles. No device validation.')

if __name__ == '__main__':
    main()
