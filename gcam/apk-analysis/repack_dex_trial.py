"""Repack an isolated DEX trial, validate DEX checksums and unchanged entries."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import zipfile
import zlib

EXPECTED = '132e18273b3aafdb93e851f5db88156bd4f82c5032ad8de6594fa5a49ea6fe89'
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('original', type=Path)
p.add_argument('dex', type=Path)
p.add_argument('output', type=Path)
p.add_argument('--label', required=True)
p.add_argument('--main-dex', type=Path, help='Also replace classes.dex for an isolated diagnostic trial')
a = p.parse_args()
original = hashlib.file_digest(a.original.open('rb'), 'sha256').hexdigest()
if original != EXPECTED: raise ValueError('Unexpected original APK')
if a.output.exists(): raise FileExistsError(a.output)
replacements = {'classes2.dex': a.dex.read_bytes()}
if a.main_dex:
    replacements['classes.dex'] = a.main_dex.read_bytes()
for name, dex in replacements.items():
    if dex[:8] != b'dex\n039\x00' or struct.unpack_from('<I', dex, 36)[0] != 112:
        raise ValueError('Expected DEX 039 with a classic 112-byte header: '+name)
    if struct.unpack_from('<I', dex, 32)[0] != len(dex): raise ValueError('Wrong DEX file size: '+name)
    if dex[12:32] != hashlib.sha1(dex[32:]).digest(): raise ValueError('Bad DEX SHA1: '+name)
    if struct.unpack_from('<I', dex, 8)[0] != zlib.adler32(dex[12:]) & 0xffffffff:
        raise ValueError('Bad DEX Adler32: '+name)
    if struct.unpack_from('<I', dex, 88)[0] > 65535: raise ValueError('Too many method references: '+name)
dex = replacements['classes2.dex']
a.output.parent.mkdir(parents=True, exist_ok=True)
with zipfile.ZipFile(a.original) as src, zipfile.ZipFile(a.output, 'w') as dst:
    for info in src.infolist():
        dst.writestr(info, replacements[info.filename] if info.filename in replacements else src.read(info))
with zipfile.ZipFile(a.original) as src, zipfile.ZipFile(a.output) as dst:
    changed = [name for name in src.namelist() if hashlib.sha256(src.read(name)).digest() != hashlib.sha256(dst.read(name)).digest()]
if sorted(changed) != sorted(replacements): raise ValueError('Unexpected changed entries: ' + repr(changed))
report = {'label': a.label, 'original_sha256': original,
          'trial_sha256': hashlib.file_digest(a.output.open('rb'), 'sha256').hexdigest(),
          'dex_sha256': hashlib.sha256(dex).hexdigest(),
          'changed_entries': changed, 'signed_update': False,
          'method_refs': struct.unpack_from('<I', dex, 88)[0],
          'dex_entries': {name: {'sha256': hashlib.sha256(data).hexdigest(),
                               'method_refs': struct.unpack_from('<I', data, 88)[0]}
                          for name, data in replacements.items()}}
a.output.with_suffix('.json').write_text(json.dumps(report, indent=2))
print(json.dumps(report, indent=2))
