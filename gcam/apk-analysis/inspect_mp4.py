"""Inspect ISO BMFF container duration, dimensions, codecs and sample counts.

Container validation is not a decoder test or a visual/audio quality assessment.
"""
import argparse
import json
from pathlib import Path
import struct

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('file', type=Path)
a = p.parse_args()
data = a.file.read_bytes()
def boxes(start, end):
    while start < end:
        if end-start < 8:
            raise ValueError('Truncated box header')
        size, kind = struct.unpack_from('>I4s', data, start)
        header = 8
        if size==1:
            size = struct.unpack_from('>Q', data, start+8)[0]
            header = 16
        elif size==0:
            size = end-start
        if size < header or start+size>end:
            raise ValueError('Invalid box extent')
        yield kind.decode('ascii'), start+header, start+size
        start += size
tracks = []
top = list(boxes(0,len(data)))
if not any(k=='mdat' for k,_,_ in top) or not any(k=='moov' for k,_,_ in top):
    raise ValueError('Missing media/movie box')
def walk(start,end,track):
    for kind,s,e in boxes(start,end):
        if kind=='trak':
            child = {}
            tracks.append(child)
            walk(s,e,child)
        elif kind in ('moov','mdia','minf','stbl'):
            walk(s,e,track)
        elif kind=='tkhd':
            width,height = struct.unpack_from('>II',data,e-8)
            track['width'],track['height'] = width/65536,height/65536
        elif kind=='mdhd':
            version = data[s]
            at = s+(20 if version==1 else 12)
            scale = struct.unpack_from('>I',data,at)[0]
            duration = struct.unpack_from('>Q' if version==1 else '>I',data,at+4)[0]
            track['duration_seconds'] = duration/scale
        elif kind=='hdlr':
            track['handler'] = data[s+8:s+12].decode('ascii')
        elif kind=='stsd':
            track['codecs'] = [k for k,_,_ in boxes(s+8,e)]
        elif kind=='stsz':
            track['samples'] = struct.unpack_from('>I',data,s+8)[0]
walk(0,len(data),{})
for track in tracks:
    if track.get('handler')=='vide' and track.get('duration_seconds'):
        track['average_fps'] = track.get('samples',0)/track['duration_seconds']
result = {'bytes': len(data), 'tracks': tracks,
          'limitation': 'Container structure and metadata only; frames/audio not decoded'}
a.file.with_suffix('.metadata.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
