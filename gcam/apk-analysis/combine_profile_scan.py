"""Add the independently verified X6810 scan6 bound to the profile-cache DEX."""
import argparse
import hashlib
from pathlib import Path
import struct
import zlib
from build_scan_trial import find_method

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('input', type=Path)
p.add_argument('output', type=Path)
a = p.parse_args()
if a.output.exists():
    raise FileExistsError(a.output)
dex = bytearray(a.input.read_bytes())
if dex[:8] != b'dex\n039\0':
    raise ValueError('Unexpected DEX format')
start, size = find_method(dex, 'Lcom/CameraLensesScan;', 'scanCameraLens')
needle = b'\x13\x02\xfa\x00'
hits = [i for i in range(start, start+size-3, 2) if dex[i:i+4] == needle]
if len(hits) != 1:
    raise ValueError('Expected exactly one scan limit instruction')
at = hits[0]
dex[at:at+4] = b'\x13\x02\x06\x00'
dex[12:32] = hashlib.sha1(dex[32:]).digest()
struct.pack_into('<I', dex, 8, zlib.adler32(dex[12:]) & 0xffffffff)
a.output.write_bytes(dex)
print('Only scan limit 250 -> 6 plus DEX checksums changed, offset:', at)
