"""Keep the full cache filename at one audited PortraitSegmenter call site.

Replace only BL dirname(data,size) with NOP. x0/x1 already hold the filename
and length, which the following string copy passes to InferenceEngine::Init.
No generic dirname helper, delegate, model, symbol or other call is changed.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct

BASELINE = '76966e7c150dfcb2795ea5b2119827a7e90b13d8c03035dbc4de583d9d12eaa6'
SITE = 0x4618e68
TARGET = 0x5f1d6dc
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('original', type=Path)
p.add_argument('output', type=Path)
a = p.parse_args()
data = a.original.read_bytes()
if hashlib.sha256(data).hexdigest() != BASELINE:
    raise ValueError('Unexpected audited native ELF')
if a.output.exists():
    raise FileExistsError(a.output)
# Audited ELF PT_LOAD covering SITE has p_offset == p_vaddr.
expected = struct.pack('<I', 0x94000000 | (((TARGET-SITE)//4)&0x3ffffff))
if data[SITE:SITE+4] != expected:
    raise ValueError('Unexpected instruction at the scoped cache-path site')
patched = data[:SITE]+struct.pack('<I',0xd503201f)+data[SITE+4:]
if patched[:SITE] != data[:SITE] or patched[SITE+4:] != data[SITE+4:]:
    raise ValueError('Unexpected native changes')
a.output.parent.mkdir(parents=True, exist_ok=True)
a.output.write_bytes(patched)
report = dict(baseline_sha256=BASELINE,
              trial_sha256=hashlib.sha256(patched).hexdigest(),
              file_offset=hex(SITE), virtual_address=hex(SITE),
              original_bytes=expected.hex(), patched_bytes=patched[SITE:SITE+4].hex(),
              changed_range_bytes=4, size=len(patched))
a.output.with_suffix('.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
