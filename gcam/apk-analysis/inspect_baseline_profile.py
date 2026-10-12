"""Audit the APK's Android P baseline profile headers against its DEX ZIP CRCs.

Read-only format 010 inspection based on AndroidX's profile reader. APK DEX
location checksums are ZIP entry CRC32, not the Adler32 in the DEX header.
"""
import argparse
import json
from pathlib import Path
import struct
import zipfile
import zlib

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('apk', type=Path)
p.add_argument('--output', type=Path, required=True)
a = p.parse_args()
with zipfile.ZipFile(a.apk) as archive:
    profile = archive.read('assets/dexopt/baseline.prof')
    if profile[:8] != b'pro\x00010\x00':
        raise ValueError('Only profile format 010 is supported')
    count = profile[8]
    raw_size, compressed_size = struct.unpack_from('<II',profile,9)
    if len(profile)!=17+compressed_size:
        raise ValueError('Unexpected profile extent')
    body = zlib.decompress(profile[17:])
    if len(body)!=raw_size:
        raise ValueError('Unexpected profile body size')
    off = 0
    rows = []
    for _ in range(count):
        key_size, classes, hot_size, checksum, methods = struct.unpack_from('<HHIII',body,off)
        key = body[off+16:off+16+key_size].decode('utf-8')
        off += 16+key_size
        name = key.split('!')[-1].split(':')[-1]
        if not name.endswith('.dex'):
            name = 'classes.dex'
        dex = archive.read(name)
        crc = archive.getinfo(name).CRC
        actual_methods = struct.unpack_from('<I',dex,88)[0]
        rows.append({'key': key, 'dex': name, 'profile_checksum': f'{checksum:08x}',
                     'apk_zip_crc32': f'{crc:08x}', 'checksum_matches': checksum==crc,
                     'profile_method_ids': methods, 'apk_method_ids': actual_methods,
                     'method_count_matches': methods==actual_methods,
                     'profile_class_count': classes, 'hot_region_bytes': hot_size})
result = {'profile_version': '010', 'profile_bytes': len(profile), 'dex_entries': rows,
          'limitation': 'Static packaged profile audit. Does not inspect current/reference runtime profiles or measure actual compilation coverage.'}
a.output.parent.mkdir(parents=True,exist_ok=True)
a.output.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
