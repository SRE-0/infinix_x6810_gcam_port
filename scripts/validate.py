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
    metadata = dict(line.split('=', 1) for line in (module / 'module.prop').read_text().splitlines() if '=' in line)
    if metadata['id'] != 'x6810_gcam_startup' or metadata['version'] != '0.7.0':
        raise ValueError('Unexpected module identity')
    print(f'PASS: {count} Python sources, native SHA-256, permission XML and V18 overlay. No device validation.')

if __name__ == '__main__':
    main()
