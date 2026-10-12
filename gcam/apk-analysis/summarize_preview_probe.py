"""Correlate diagnostic startup events and paired provider/call timing sites."""
import argparse
import json
from pathlib import Path
import re

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('directory', type=Path)
p.add_argument('label')
p.add_argument('--catalog', type=Path)
a = p.parse_args()
catalog = {s['id']: s for s in json.loads((a.catalog or a.directory/'sites.json').read_text())}
out = a.directory/'measurements'/a.label
log = (out/'app-logcat.txt').read_text()
events = []
calls = []
sites = []
pending = {}
fields = {}
for line in log.splitlines():
    event = re.search(r'\s(\d+)\s+(\d+)\s+I X6810_PREVIEW: event=(\w+) raw_ns=(\d+)', line)
    if event:
        pid, tid, name, ns = event.groups()
        events.append({'pid': int(pid), 'tid': int(tid), 'name': name, 'ns': int(ns)})
    site = re.search(r'\s(\d+)\s+(\d+)\s+I X6810_PREVIEW: site=(\d+) now_ns=(\d+)', line)
    if not site:
        continue
    pid, tid, index, ns = map(int, site.groups())
    definition = catalog[index]
    sites.append(dict(definition, pid=pid, tid=tid, ns=ns))
    if definition['kind'] == 'provider_field':
        fields[tid] = definition['instruction']
    elif definition['kind'] == 'call_begin':
        pending.setdefault((tid, index), []).append((ns, fields.get(tid)))
    elif definition['kind'] == 'call_end':
        stack = pending.get((tid, definition['pair']), [])
        if not stack:
            continue
        begin, field = stack.pop()
        calls.append(dict(definition, start_ns=begin, tid=tid, duration_ms=round((ns-begin)/1e6, 3),
                          provider_field=field if 'jpq.smali' in definition['file'] and 'Luhb;->a()' in definition['instruction'] else None))
origin = next(e['ns'] for e in events if e['name']=='ACTIVITY_ONCREATE_START')
for item in events+sites:
    item['from_oncreate_ms'] = round((item['ns']-origin)/1e6, 3)
for item in calls:
    item['from_oncreate_ms'] = round((item['start_ns']-origin)/1e6, 3)
jpq = sorted((s for s in sites if 'jpq.smali' in s['file']), key=lambda s: s['ns'])
gaps = [{'duration_ms': round((right['ns']-left['ns'])/1e6, 3),
         'before': left, 'after': right} for left, right in zip(jpq, jpq[1:])
        if right['ns']-left['ns']>8_000_000]
result = {'label': a.label, 'events': events, 'calls': sorted(calls, key=lambda c: -c['duration_ms']),
          'jpq_gaps': gaps,
          'sites': sites, 'limitation': 'Diagnostic APK and logging alter timing. Not an optimization benchmark.'}
(out/'preview-probe-summary.json').write_text(json.dumps(result, indent=2)+'\n')
print(json.dumps({'events': events, 'slow_calls': result['calls'][:12], 'jpq_gaps': gaps}, indent=2))
