"""Repack only the main DEX of the hash-guarded retained GCam 0.2.0 APK."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import zipfile
import zlib

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('apk', type=Path)
p.add_argument('dex', type=Path)
p.add_argument('output', type=Path)
a = p.parse_args()
expected = '628012f407d7df89b6d7064cc5be6e103d4a0652de7123ddddd4a2295b17759d'
if hashlib.file_digest(a.apk.open('rb'), 'sha256').hexdigest() != expected:
    raise ValueError('Unexpected retained APK')
if a.output.exists():
    raise FileExistsError(a.output)
d = a.dex.read_bytes()
if d[:8] != b'dex\n039\0' or struct.unpack_from('<I', d, 32)[0] != len(d):
    raise ValueError('Invalid DEX header')
if d[12:32] != hashlib.sha1(d[32:]).digest() or struct.unpack_from('<I', d, 8)[0] != zlib.adler32(d[12:]) & 0xffffffff:
    raise ValueError('Invalid DEX checksums')
refs = struct.unpack_from('<I', d, 88)[0]
if refs > 65535:
    raise ValueError('Main DEX reference limit exceeded')
with zipfile.ZipFile(a.apk) as src, zipfile.ZipFile(a.output, 'w') as dst:
    for entry in src.infolist():
        dst.writestr(entry, d if entry.filename == 'classes.dex' else src.read(entry))
with zipfile.ZipFile(a.apk) as src, zipfile.ZipFile(a.output) as dst:
    changed = [n for n in src.namelist() if src.read(n) != dst.read(n)]
if changed != ['classes.dex']:
    raise ValueError('Unexpected ZIP changes: '+repr(changed))
report = {'baseline_sha256': expected,
          'trial_sha256': hashlib.file_digest(a.output.open('rb'), 'sha256').hexdigest(),
          'changed_entries': changed, 'main_method_refs': refs, 'signed_update': False}
a.output.with_suffix('.json').write_text(json.dumps(report, indent=2)+'\n')
print(json.dumps(report, indent=2))
