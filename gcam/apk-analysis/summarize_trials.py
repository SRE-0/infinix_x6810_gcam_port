"""Summarize all compiled APK trial runs, without silently removing outliers."""
import argparse
import json
from pathlib import Path
import statistics

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('directory', type=Path)
a = p.parse_args()
timings = json.loads((a.directory/'measurements/timings.json').read_text())
groups = {}
for prefix in ('original_compiled_', 'scan6_compiled_', 'nolog_compiled_'):
    rows = [r for r in timings['runs'] if r['label'].startswith(prefix)]
    ttid = [r['ttid_ms'] for r in rows]
    proxy = [r['controls_log_proxy_ms'] for r in rows if r['controls_log_proxy_ms'] is not None]
    groups[prefix] = {'n': len(rows), 'labels': [r['label'] for r in rows],
                      'median_ttid_ms': statistics.median(ttid),
                      'range_ttid_ms': [min(ttid), max(ttid)],
                      'median_controls_proxy_ms': statistics.median(proxy)}
base = groups['original_compiled_']['median_ttid_ms']
for g in groups.values():
    g['ttid_delta_vs_original_ms'] = round(g['median_ttid_ms']-base, 2)
    g['ttid_reduction_vs_original_percent'] = round(100*(base-g['median_ttid_ms'])/base, 2)
captures = {}
for name in ('capture-original-3s-final', 'capture-scan6-3s-final'):
    captures[name] = json.loads((a.directory/name/'result.json').read_text())
result = {'compiled_runs': groups, 'all_runs': timings['runs'], 'captures': captures,
          'limitations': ['Process-cold launches with warm filesystem caches; no reboot comparison.',
                          'Small, sequential blocks; temperature/profile learning can confound results.',
                          'TTID and controls log proxy are not first stable preview or TTFD.',
                          'Temporary bind mounts, not a signed package-manager install.',
                          'Exploratory uncompiled runs remain in all_runs. No compiled outlier removed.']}
(a.directory/'comparison.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
print(json.dumps(groups, indent=2))
