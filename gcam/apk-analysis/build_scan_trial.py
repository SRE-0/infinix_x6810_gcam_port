"""Build a narrowly scoped DEX patch; never edits the original APK.

The output retains old signature entries and is NOT installable as a signed
update. It is intended only for a temporary root bind-mount experiment.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import zipfile
import zlib

EXPECTED = '132e18273b3aafdb93e851f5db88156bd4f82c5032ad8de6594fa5a49ea6fe89'

def find_method(d, class_name, method_name):
    def u32(o): return struct.unpack_from('<I', d, o)[0]
    def uleb(o):
        value = shift = 0
        while True:
            b = d[o]; o += 1
            value |= (b & 127) << shift
            if not b & 128: return value, o
            shift += 7
            if shift > 35: raise ValueError('Invalid ULEB128')
    ns, os = u32(56), u32(60)
    strings = []
    for i in range(ns):
        start = u32(os + 4*i)
        _, start = uleb(start)
        end = d.index(0, start)
        strings.append(bytes(d[start:end]).decode('utf-8', errors='replace'))
    nt, ot = u32(64), u32(68)
    types = [strings[u32(ot + 4*i)] for i in range(nt)]
    nm, om = u32(88), u32(92)
    methods = [struct.unpack_from('<HHI', d, om + 8*i) for i in range(nm)]
    nc, oc = u32(96), u32(100)
    for i in range(nc):
        base = oc + 32*i
        if types[u32(base)] != class_name: continue
        off = u32(base + 24)
        counts = []
        for _ in range(4):
            v, off = uleb(off); counts.append(v)
        for _ in range(counts[0] + counts[1]):
            _, off = uleb(off); _, off = uleb(off)
        for count in counts[2:]:
            index = 0
            for _ in range(count):
                delta, off = uleb(off); index += delta
                _, off = uleb(off); code, off = uleb(off)
                if strings[methods[index][2]] == method_name:
                    size = u32(code + 12)*2
                    return code + 16, size
    raise ValueError(f'{class_name}.{method_name} not found')

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('original', type=Path)
    p.add_argument('output', type=Path)
    p.add_argument('--variant', choices=['scan6', 'nolog'], default='scan6')
    a = p.parse_args()
    original_hash = hashlib.file_digest(a.original.open('rb'), 'sha256').hexdigest()
    if original_hash != EXPECTED: raise ValueError('Unexpected original APK')
    if a.output.exists(): raise FileExistsError(a.output)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(a.original) as src:
        before = src.read('classes.dex')
        dex = bytearray(before)
        if a.variant == 'scan6':
            start, size = find_method(dex, 'Lcom/CameraLensesScan;', 'scanCameraLens')
            # const/16 v2, 250, independently verified against this APK's smali.
            pattern = b'\x13\x02\xfa\x00'
            hits = [i for i in range(start, start + size - 3, 2) if dex[i:i+4] == pattern]
            if len(hits) != 1: raise ValueError(f'Expected one matching instruction: {hits}')
            hit = hits[0]
            replacement = b'\x13\x02\x06\x00'
        else:
            hit, size = find_method(dex, 'Lcom/b;', 'StartLogging')
            pattern = bytes(dex[hit:hit+6])
            if pattern[:2] != b'\x2a\x00': raise ValueError('Expected initial goto/32')
            # Replace exactly one 3-code-unit instruction with return + two NOPs.
            replacement = b'\x0e\x00\x00\x00\x00\x00'
        dex[hit:hit+len(replacement)] = replacement
        dex[12:32] = hashlib.sha1(dex[32:]).digest()
        struct.pack_into('<I', dex, 8, zlib.adler32(dex[12:]) & 0xffffffff)
        changed = [i for i in range(len(dex)) if dex[i] != before[i]]
        if any(i >= 32 and not hit <= i < hit+len(replacement) for i in changed):
            raise ValueError('Unexpected DEX mutation')
        # Keep resources, manifest, other DEX and libraries byte-identical when
        # uncompressed. ZIP signing blocks are not preserved by repacking.
        with zipfile.ZipFile(a.output, 'w') as dst:
            for info in src.infolist():
                dst.writestr(info, bytes(dex) if info.filename == 'classes.dex' else src.read(info))
    with zipfile.ZipFile(a.original) as src, zipfile.ZipFile(a.output) as dst:
        diff = [i for i in src.namelist() if hashlib.sha256(src.read(i)).digest() !=
                hashlib.sha256(dst.read(i)).digest()]
    if diff != ['classes.dex']: raise ValueError(diff)
    report = {'original_sha256': original_hash,
              'trial_sha256': hashlib.file_digest(a.output.open('rb'), 'sha256').hexdigest(),
              'changed_zip_entries': diff, 'dex_instruction_offset': hit,
              'variant': a.variant,
              'before_hex': pattern.hex(), 'after_hex': dex[hit:hit+len(replacement)].hex(),
              'device_scope': 'X6810: service devices 0,1,2,3,4,5 verified in dumpsys',
              'signed_update': False}
    a.output.with_suffix('.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))

if __name__ == '__main__': main()
