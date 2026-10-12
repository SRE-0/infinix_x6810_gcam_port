"""Prepare a bounded native-only worker on top of retained 0.2.0 sources."""
from helper_templates import helper_path
from pathlib import Path
import argparse
import shutil

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('secondary', type=Path)
p.add_argument('output', type=Path)
a = p.parse_args()
target = a.output / 'smali_classes2'
shutil.copytree(a.secondary, target)
app = target / 'com/google/android/apps/camera/legacy/app/app/CameraApp.smali'
s = app.read_text(encoding='utf-8')
needle = '.method public final onCreate()V\n    .locals 32\n'
if s.count(needle) != 1 or 'Lx6810/gcam/NativeProfileWarm;' in s:
    raise ValueError('Unexpected application hook')
app.write_text(s.replace(needle, needle + '\n    invoke-static {}, Lx6810/gcam/NativeProfileWarm;->start()V\n'), encoding='utf-8')
shutil.copyfile(helper_path('NativeProfileWarm.smali'), target/'x6810/gcam/NativeProfileWarm.smali')
print('Prepared one native-only background initialization; no UI or preference access')
