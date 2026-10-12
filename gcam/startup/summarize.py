"""Summarize existing ADB startup captures; readiness is a log proxy, not TTFD."""
import argparse
from datetime import datetime, timedelta
import json
from pathlib import Path
import statistics

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('directory', type=Path)
a = p.parse_args()
rows = []
for path in sorted(a.directory.glob('*/summary.json')):
    s = json.loads(path.read_text())
    lines = (path.parent / 'timeline.txt').read_text().splitlines()
    marker = next((x for x in lines if 'X6810_STARTUP:' in x), None)
    enabled = next((x for x in lines if 'ModeSwitcher WAS ALREADY ENABLED!' in x), None)
    def stamp(line):
        return datetime.strptime('2000-' + line[:18], '%Y-%m-%d %H:%M:%S.%f')
    proxy = None
    if marker and enabled:
        delta = stamp(enabled) - stamp(marker)
        if delta < timedelta():
            delta += timedelta(days=1)
        proxy = round(delta.total_seconds() * 1000)
    rows.append({'label': s['label'], 'ttid_ms': s['initial_display_ms'],
                 'controls_log_proxy_ms': proxy,
                 'preview_ready_ms': s['preview_ready_ms']})
groups = {}
for prefix in ('control_', 'speed_', 'eager_ui_'):
    subset = [r for r in rows if r['label'].startswith(prefix)]
    if subset:
        groups[prefix] = {'n': len(subset), 'median_ttid_ms': statistics.median(r['ttid_ms'] for r in subset),
                         'median_controls_log_proxy_ms': statistics.median(r['controls_log_proxy_ms'] for r in subset if r['controls_log_proxy_ms'] is not None)}
result = {'runs': rows, 'groups': groups,
          'limitation': 'ModeSwitcher warning is a proxy. No claim of preview readiness or capture latency.'}
(a.directory / 'timings.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(groups, indent=2))
