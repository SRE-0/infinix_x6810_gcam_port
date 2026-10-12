"""Summarize ABBA trials using existing app events and the ADB launch marker.

Marker-to-event estimates include host/ADB launch overhead; these are neither
physical touch latency nor proof of a displayed frame. Do not substitute TTID.
"""
import argparse
from datetime import datetime, timedelta
import json
from pathlib import Path
import statistics

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('directory', type=Path)
p.add_argument('--prefix', required=True)
p.add_argument('--exclude-label', action='append', default=[], help='Retain but exclude a run with a documented interference')
a = p.parse_args()
rows = json.loads((a.directory/(a.prefix+'-results.json')).read_text())
for row in rows:
    row['included'] = row['label'] not in a.exclude_label
    out = a.directory/'measurements'/row['label']
    logs = (out/'logcat.txt').read_text(errors='replace').splitlines()
    marker = next(s for s in logs if 'X6810_STARTUP:' in s and row['label'] in s)
    oncreate = next(s for s in logs if 'X6810_PREVIEW:' in s and 'event=ACTIVITY_ONCREATE_START ' in s)
    stamp = lambda s: datetime.strptime('2000-'+s[:18], '%Y-%m-%d %H:%M:%S.%f')
    delta = stamp(oncreate)-stamp(marker)
    if delta < timedelta():
        delta += timedelta(days=1)
    offset = delta.total_seconds()*1000
    ev = row['events_ms']
    row['marker_to_oncreate_ms'] = round(offset, 3)
    row['marker_to_events_ms'] = {k: round(offset+v, 3) for k,v in ev.items()}
    row['controller_initialization_ms'] = round(ev['ACTIVITY_INITIALIZED']-ev['ACTIVITY_INITIALIZE_START'], 3)
    row['ui_wire_ms'] = round(ev['ACTIVITY_UI_WIRE_END']-ev['ACTIVITY_UI_WIRE_START'], 3)
groups = {}
for variant in sorted(set(row['variant'] for row in rows)):
    chosen = [r for r in rows if r['variant']==variant and r['included']]
    values = {'ttid_ms': [r['initial_display_ms'] for r in chosen],
              'controller_initialization_ms': [r['controller_initialization_ms'] for r in chosen],
              'ui_wire_ms': [r['ui_wire_ms'] for r in chosen]}
    for event in ('ACTIVITY_FIRST_PREVIEW_FRAME_RECEIVED', 'ACTIVITY_FIRST_PREVIEW_FRAME_VFE_RENDERED',
                  'ACTIVITY_FIRST_PREVIEW_FRAME_RENDERED', 'ACTIVITY_SHUTTER_BUTTON_ENABLED', 'ACTIVITY_STEADY'):
        values['marker_to_'+event] = [r['marker_to_events_ms'][event] for r in chosen if event in r['marker_to_events_ms']]
    groups[variant] = {'n': len(chosen), 'fatal_count': sum(r['fatal'] for r in chosen),
                       **{k: {'median': statistics.median(v), 'min': min(v), 'max': max(v)} for k,v in values.items() if v}}
result = {'groups': groups, 'runs': rows, 'limitation':
          'Small process-cold sample, warm filesystem. Diagnostic event logging identical. Marker estimates include ADB overhead. No statistical significance or photographic quality improvement claim.'}
(a.directory/(a.prefix+'-summary.json')).write_text(json.dumps(result, indent=2)+'\n')
print(json.dumps(groups, indent=2))
