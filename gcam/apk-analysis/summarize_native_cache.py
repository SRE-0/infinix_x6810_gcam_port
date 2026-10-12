"""Summarize ABBA native cache diagnostics without conflating readiness metrics."""
import argparse
import json
from pathlib import Path
import re
import statistics

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('directory', type=Path)
a = p.parse_args()
rows = []
for folder in sorted(a.directory.glob('g*')):
    if folder.name.endswith('warmup') or not (folder/'app-logcat.txt').exists():
        continue
    logs = (folder/'app-logcat.txt').read_text(errors='replace')
    events = {k:int(v) for k,v in re.findall(r'X6810_PREVIEW:\s*event=(\w+) raw_ns=(\d+)',logs)}
    marks = [(phase,int(ns)) for phase,ns in re.findall(
        r'X6810_REMAINING:\s*site=189 phase=(begin|end) now_ns=(\d+)',logs)]
    if len(marks) != 2 or [x[0] for x in marks] != ['begin','end']:
        raise RuntimeError('Missing/unexpected primary init pair: '+folder.name)
    origin = events['ACTIVITY_ONCREATE_START']
    rows.append(dict(label=folder.name, patched='_patched_' in folder.name,
                     initial_display_ms=json.loads((folder/'summary.json').read_text())['initial_display_ms'],
                     segmenter_init_ms=(marks[1][1]-marks[0][1])/1e6,
                     segmenter_init_end_from_oncreate_ms=(marks[1][1]-origin)/1e6,
                     first_preview_from_oncreate_ms=(events['ACTIVITY_FIRST_PREVIEW_FRAME_RENDERED']-origin)/1e6,
                     shutter_from_oncreate_ms=(events['ACTIVITY_SHUTTER_BUTTON_ENABLED']-origin)/1e6,
                     cache_error='Failed to updated cache' in logs,
                     inference_error='Could not initialize inference engine' in logs,
                     java_gl_fallback='OpenCL segmenter failed to produce a reasonable mask' in logs,
                     fatal=any(s in logs for s in ('FATAL EXCEPTION','Fatal signal','ANR in'))))
summary = {}
for patched in (False,True):
    selected = [r for r in rows if r['patched'] == patched]
    if not selected:
        continue
    summary['patched' if patched else 'original'] = dict(
        runs=len(selected),
        medians={k:statistics.median(r[k] for r in selected) for k in
                 ('initial_display_ms','segmenter_init_ms','segmenter_init_end_from_oncreate_ms',
                  'first_preview_from_oncreate_ms','shutter_from_oncreate_ms')},
        counts={k:sum(r[k] for r in selected) for k in
                ('cache_error','inference_error','java_gl_fallback','fatal')})
report = dict(rows=rows,summary=summary,
              note='Process-cold, warm filesystem; warmups excluded. Java init duration is not app TTFD.')
(a.directory/'results.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(summary,indent=2))
