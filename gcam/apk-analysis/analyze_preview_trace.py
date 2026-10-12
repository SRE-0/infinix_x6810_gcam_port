"""Export an app's startup slices from a root ftrace using official trace_processor."""
import argparse
import csv
import json
import re
from pathlib import Path
import subprocess

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('trace', type=Path)
p.add_argument('--pid', type=int, required=True)
p.add_argument('--processor', type=Path, required=True)
a = p.parse_args()
with a.trace.open(errors='replace') as stream:
    header = ''.join(next(stream, '') for _ in range(10))
counts = re.search(r'entries-in-buffer/entries-written:\s*(\d+)/(\d+)', header)
quality = {'buffer_counts_available': bool(counts)}
if counts:
    quality.update(entries_in_buffer=int(counts[1]), entries_written=int(counts[2]),
                   overwritten_events=int(counts[2])-int(counts[1]))
    if quality['overwritten_events']:
        raise RuntimeError('Trace buffer overwrote events; recollect with a larger buffer before interpreting nested spans')
query = f"""
SELECT s.id,s.parent_id,s.ts,s.dur,s.name,ifnull(t.tid,0) tid
FROM slice s
LEFT JOIN thread_track tt ON tt.id=s.track_id
LEFT JOIN thread t USING(utid)
LEFT JOIN process_track pt ON pt.id=s.track_id
WHERE (t.upid=(SELECT upid FROM process WHERE pid={a.pid})
       OR pt.upid=(SELECT upid FROM process WHERE pid={a.pid}))
AND s.dur>=0 AND (s.dur>=1000000 OR s.name GLOB '*First*'
 OR s.name GLOB '*WaitFor*' OR s.name GLOB '*IC.*' OR s.name GLOB '*CameraId*')
ORDER BY s.ts;
"""
sql = a.trace.parent/'app-slices.sql'
sql.write_text(query)
out = a.trace.parent/'app-slices.csv'
with out.open('wb') as stream, (a.trace.parent/'processor.log').open('wb') as err:
    subprocess.run([str(a.processor), str(a.trace), '-q', str(sql)], stdout=stream,
                   stderr=err, check=True)
rows = list(csv.DictReader(out.open()))
origin = next(int(r['ts']) for r in rows if r['name']=='bindApplication')
def relative(row):
    return {'name': row['name'], 'tid': int(row['tid']),
            'start_ms': round((int(row['ts'])-origin)/1e6, 3),
            'duration_ms': round(int(row['dur'])/1e6, 3),
            'end_ms': round((int(row['ts'])+int(row['dur'])-origin)/1e6, 3)}
interesting = [relative(r) for r in rows if
               any(s in r['name'] for s in ('First', 'CameraActivity', 'UiWirer', 'cameraUiModule',
                   'setModuleFromMode', 'getModuleController', 'WaitFor', 'IC.', 'Viewfinder',
                   'bindApplication', 'makeApplication', 'GCA_App#', 'OpenCamera', 'OneCameraCreator'))]
main = [relative(r) for r in rows if int(r['tid'])==a.pid and int(r['dur'])>=15000000
        and origin<=int(r['ts'])<origin+5_000_000_000]
result = {'pid': a.pid, 'origin': 'bindApplication', 'interesting': interesting,
          'trace_quality': quality,
          'main_slices': main,
          'limitation': 'Nested spans must not be added. FirstPreviewFrame is an app signal, not proof of physical display.'}
(a.trace.parent/'preview-trace-summary.json').write_text(json.dumps(result, indent=2)+'\n')
print(json.dumps(interesting[:50], indent=2))
