"""Summarize threading trials without treating initial display as camera readiness."""
import argparse
from datetime import datetime, timedelta
import json
from pathlib import Path
import re
import statistics

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('directory', type=Path)
a = p.parse_args()
rows = []
for path in sorted(a.directory.glob('*/summary.json')):
    summary = json.loads(path.read_text())
    lines = (path.parent/'timeline.txt').read_text().splitlines()
    marker = next((s for s in lines if 'X6810_STARTUP:' in s), None)
    enabled = next((s for s in lines if 'ModeSwitcher WAS ALREADY ENABLED!' in s), None)
    proxy = None
    if marker and enabled:
        stamp = lambda s: datetime.strptime('2000-'+s[:18], '%Y-%m-%d %H:%M:%S.%f')
        delta = stamp(enabled)-stamp(marker)
        if delta < timedelta():
            delta += timedelta(days=1)
        proxy = round(delta.total_seconds()*1000)
    log = (path.parent/'app-logcat.txt').read_text()
    workers = re.findall(r'^\S+\s+\S+\s+(\d+)\s+(\d+)\s+I X6810_THREADING: worker end elapsed_ms=(\d+) loaded=(\d+)', log, re.M)
    exclusions = {
        'fonts39_01': 'ART compile started while initial APK apply was pending; compile target unconfirmed',
        'fonts39_02': 'Same unconfirmed ART compile as fonts39_01',
        'fonts39_03': 'Concurrent UI dump for capture probe; retained for audit',
    }
    exclusion = exclusions.get(summary['label'])
    rows.append({'label': summary['label'], 'ttid_ms': summary['initial_display_ms'],
                 'controls_log_proxy_ms': proxy, 'worker_results': workers,
                 'preview_ready_ms': None,
                 'included': exclusion is None,
                 'exclusion': exclusion})
groups = {}
for prefix in ('original_', 'control39_', 'worker39_', 'fonts39_'):
    subset = [r for r in rows if r['included'] and r['label'].startswith(prefix)]
    if not subset:
        continue
    group = {'n': len(subset)}
    for key in ('ttid_ms', 'controls_log_proxy_ms'):
        values = [r[key] for r in subset if r[key] is not None]
        group[key] = {'median': statistics.median(values), 'min': min(values), 'max': max(values)} if values else None
    groups[prefix] = group
result = {'runs': rows, 'groups': groups,
          'limitation': 'Process-cold, filesystem warm. Log proxy is not TTFD. Small samples, no statistical significance claim.'}
(a.directory/'thread-timings.json').write_text(json.dumps(result, indent=2)+'\n')
print(json.dumps(groups, indent=2))
