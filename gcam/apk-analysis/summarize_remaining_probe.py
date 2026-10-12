"""Pair version-specific Java diagnostic sites by site and Linux TID."""
import argparse
import json
from pathlib import Path
import re

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('sites', type=Path)
p.add_argument('logs', type=Path)
p.add_argument('--output', type=Path)
a = p.parse_args()
sites = {s['id']: s for s in json.loads(a.sites.read_text())}
pending = {}
rows = []
unmatched = []
for line in a.logs.read_text(errors='replace').splitlines():
    m = re.search(r'\s(\d+)\s+(\d+)\s+I\s+X6810_REMAINING\s*:\s*site=(\d+) phase=(begin|end) now_ns=(\d+)', line)
    if not m:
        continue
    pid, tid, site, phase, ns = m.groups()
    key = (pid, tid, int(site))
    if phase == 'begin':
        if key in pending:
            unmatched.append(dict(key=key, error='duplicate begin'))
        pending[key] = int(ns)
    elif key in pending:
        rows.append(dict(site=int(site), pid=int(pid), tid=int(tid),
                         elapsed_ms=(int(ns)-pending.pop(key))/1e6,
                         instruction=sites[int(site)]['instruction'],
                         file=sites[int(site)]['file']))
    else:
        unmatched.append(dict(key=key, error='end without begin'))
rows.sort(key=lambda r: r['elapsed_ms'], reverse=True)
report = dict(pairs=rows, unmatched=unmatched,
              pending=[dict(key=k, begin_ns=v) for k,v in pending.items()])
if a.output:
    a.output.write_text(json.dumps(report, indent=2)+'\n')
print(json.dumps(dict(top=rows[:15], total_pairs=len(rows),
                     unmatched=unmatched, pending=report['pending']), indent=2))
