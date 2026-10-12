"""Prepare a thread-prewarm DEX experiment in an isolated smali copy."""
from helper_templates import helper_path
import argparse
from pathlib import Path
import json

CLASSES = ['kkh', 'kkf', 'kkb', 'kkc', 'kkd', 'kka', 'kjt', 'kdg', 'gpk', 'jnr',
           'glc', 'gll', 'gsr', 'mcg', 'gle', 'nmj', 'mrj', 'mnk', 'lwi', 'lwl',
           'jix', 'ncz', 'gqj', 'nne', 'mpy', 'iin', 'iht', 'moc', 'mdh', 'lgc',
           'msd', 'nit', 'nsu', 'nsk', 'nsw', 'nsp', 'nqe', 'nni', 'nba', 'mjn',
           'jnf', 'jnh', 'gmg', 'hzs', 'joc', 'jnx']
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('directory', type=Path)
p.add_argument('--original-smali', type=Path, required=True)
a = p.parse_args()
target = a.directory/'smali_classes2'
app = target/'com/google/android/apps/camera/legacy/app/app/CameraApp.smali'
text = app.read_text(encoding='utf-8')
needle = '.method public final onCreate()V\n    .locals 32\n'
if text.count(needle) != 1 or 'Lx6810/gcam/StartupWorker;' in text:
    raise ValueError('Unexpected CameraApp method or already modified')
for name in CLASSES:
    if not any((folder/(name+'.smali')).exists() for folder in a.original_smali.glob('smali*')):
        raise ValueError('Class not verified in APK: ' + name)
app.write_text(text.replace(needle, needle + '\n    invoke-static/range {p0 .. p0}, Lx6810/gcam/StartupWorker;->start(Landroid/content/Context;)V\n'), encoding='utf-8')
worker = helper_path('StartupWorker.smali').read_text(encoding='utf-8')
preloads = '\n'.join('    const-string v3, "'+name+'"\n    invoke-direct {p0, v3}, Lx6810/gcam/StartupWorker;->load(Ljava/lang/String;)V' for name in CLASSES)
dest = target/'x6810/gcam/StartupWorker.smali'
dest.parent.mkdir(parents=True, exist_ok=True)
dest.write_text(worker.replace('    # GENERATED_PRELOADS', preloads), encoding='utf-8')
(a.directory/'preload-classes.json').write_text(json.dumps(CLASSES, indent=2))
print('Prepared background linking of', len(CLASSES), 'verified classes')
