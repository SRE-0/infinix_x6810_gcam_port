"""Correlate startup/UI slices with main-thread CPU and scheduling states."""
import argparse
import csv
import json
from pathlib import Path
import subprocess

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('trace', type=Path)
p.add_argument('--pid', type=int, required=True)
p.add_argument('--processor', type=Path, required=True)
a = p.parse_args()
query = f"""
WITH windows AS (
 SELECT s.id,s.name,s.ts,s.dur,t.utid
 FROM slice s JOIN thread_track tt ON tt.id=s.track_id JOIN thread t USING(utid)
 WHERE t.tid={a.pid} AND t.upid=(SELECT upid FROM process WHERE pid={a.pid} LIMIT 1)
 AND s.dur>0 AND s.name IN ('bindApplication','makeApplication','CameraActivity#onCreate',
 'CameraActivityControllerInitializer#initialize','UiWirer#wire',
 'OptionsBarCtrl#wireAutobahn','updateOptionsBar','cameraUiModule#inflate',
 'getModuleController for: 1')
)
SELECT w.id,w.name,w.dur/1e6 wall_ms,coalesce(t.state,'unknown') state,
 sum(min(t.ts+t.dur,w.ts+w.dur)-max(t.ts,w.ts))/1e6 state_ms
FROM windows w JOIN thread_state t ON t.utid=w.utid AND t.dur>0
 AND t.ts<w.ts+w.dur AND t.ts+t.dur>w.ts
GROUP BY w.id,t.state ORDER BY w.ts,state_ms DESC;
"""
out = a.trace.parent/'main-states.csv'
sql = out.with_suffix('.sql')
sql.write_text(query)
with out.open('wb') as stream, out.with_suffix('.processor.log').open('wb') as err:
    subprocess.run([str(a.processor),str(a.trace),'-q',str(sql)],stdout=stream,stderr=err,check=True)
rows = list(csv.DictReader(out.open()))
groups = {}
for row in rows:
    group = groups.setdefault(row['id'], {'name': row['name'], 'wall_ms': float(row['wall_ms']), 'states_ms': {}})
    group['states_ms'][row['state']] = float(row['state_ms'])
result = {'windows': list(groups.values()), 'limitation':
          'State coverage depends on trace parsing. Windows are nested and not additive. Runnable indicates scheduling delay, not CPU execution.'}
out.with_suffix('.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
coquery = f"""
WITH windows AS (
 SELECT s.ts,s.dur FROM slice s JOIN thread_track tt ON tt.id=s.track_id
 JOIN thread t USING(utid) WHERE t.tid={a.pid} AND s.name='updateOptionsBar' AND s.dur>0
)
SELECT p.name process,t.name thread,t.tid,
 sum(min(sc.ts+sc.dur,w.ts+w.dur)-max(sc.ts,w.ts))/1e6 running_ms
FROM windows w JOIN sched sc ON sc.dur>0 AND sc.ts<w.ts+w.dur AND sc.ts+sc.dur>w.ts
 JOIN thread t USING(utid) LEFT JOIN process p USING(upid)
GROUP BY t.utid ORDER BY running_ms DESC LIMIT 15;
"""
cosql = out.with_name('options-corunners.sql')
cosql.write_text(coquery)
with out.with_name('options-corunners.csv').open('wb') as stream:
    subprocess.run([str(a.processor),str(a.trace),'-q',str(cosql)],stdout=stream,stderr=subprocess.DEVNULL,check=True)
