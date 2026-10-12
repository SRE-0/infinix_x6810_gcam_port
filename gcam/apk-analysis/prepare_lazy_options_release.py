"""Remove timing instrumentation from an isolated, tested lazy-options tree."""
import argparse
from pathlib import Path
import shutil

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('trial_secondary', type=Path)
p.add_argument('original_secondary', type=Path)
p.add_argument('output', type=Path)
a = p.parse_args()
for source in (a.trial_secondary, a.original_secondary):
    if a.output.resolve() == source.resolve() or source.resolve() in a.output.resolve().parents:
        raise ValueError('Output must be isolated')
if a.output.exists():
    raise FileExistsError(a.output)
instrumented = (a.trial_secondary/'mqt.smali').read_text(encoding='utf-8')
if instrumented.count('Lx6810/gcam/StartupTimeline;->record(') != 1:
    raise ValueError('Unexpected diagnostic instrumentation')
shutil.copytree(a.trial_secondary, a.output)
shutil.copyfile(a.original_secondary/'mqt.smali', a.output/'mqt.smali')
(a.output/'x6810/gcam/StartupTimeline.smali').unlink()
print('Prepared lazy options release without diagnostic timing logging')
