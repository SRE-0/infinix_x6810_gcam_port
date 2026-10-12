"""Prepare an isolated diagnostic APK: existing timing events and startup call sites."""
import argparse
import json
from pathlib import Path
import re
import shutil

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('original_smali', type=Path)
p.add_argument('output', type=Path)
p.add_argument('--reuse-copy', action='store_true', help='Reset modified files in an existing isolated copy')
a = p.parse_args()
if a.output.resolve() == a.original_smali.resolve() or a.original_smali.resolve() in a.output.resolve().parents:
    raise ValueError('Output must be separate from the original extraction')
if a.output.exists() and not a.reuse_copy:
    raise FileExistsError(a.output)
if not a.reuse_copy:
    a.output.mkdir(parents=True)
    for folder in ('smali', 'smali_classes2'):
        shutil.copytree(a.original_smali/folder, a.output/folder)
catalog = []

def site(path, method, line, instruction, kind, pair=None):
    index = len(catalog)+1
    catalog.append(dict(id=index, file=str(path), method=method, original_line=line,
                        instruction=instruction.strip(), kind=kind, pair=pair))
    return index

def mark(register, index):
    return [f'    const/16 v{register}, {index}',
            f'    invoke-static/range {{v{register} .. v{register}}}, Lx6810/gcam/StartupTimeline;->mark(I)V']

def instrument(relative, method_selector, call_selector, fields=False, entry=False):
    path = a.output/relative
    lines = (a.original_smali/relative).read_text(encoding='utf-8').splitlines()
    result = []
    method = None
    active = False
    scratch = None
    pending = None
    for number, line in enumerate(lines, 1):
        if line.startswith('.method '):
            method = line
            active = method_selector(line)
        if active and re.match(r'\s+\.locals \d+$', line):
            scratch = int(line.split()[-1])
            # Parameters must already use symbolic p registers. All added invokes
            # use /range, and the scratch register fits const/16's destination.
            if scratch >= 255:
                raise ValueError('No byte-addressable scratch register: '+method)
            result.append(f'    .locals {scratch+1}')
            if entry:
                result.extend(mark(scratch, site(relative, method, number, 'method entry', 'entry')))
            continue
        if active and call_selector(line):
            start = site(relative, method, number, line, 'call_begin')
            result.extend(mark(scratch, start))
            pending = (start, line, number)
            result.append(line)
            # Results may deliberately be discarded. Keep an actual move-result
            # adjacent to its invoke, otherwise end immediately after the call.
            next_code = next((s.strip() for s in lines[number:] if s.strip() and not s.strip().startswith(('#', '.line', '.local', '.prologue'))), '')
            if not next_code.startswith('move-result'):
                result.extend(mark(scratch, site(relative, method, number, line, 'call_end', start)))
                pending = None
            continue
        result.append(line)
        if pending and line.strip().startswith('move-result'):
            start, instruction, call_line = pending
            result.extend(mark(scratch, site(relative, method, call_line, instruction, 'call_end', start)))
            pending = None
        elif pending and line.strip() and not line.strip().startswith(('#', '.line')):
            raise ValueError('Expected adjacent move-result after: '+pending[1])
        if active and fields and 'iget-object' in line and 'Ljpq;->' in line:
            result.extend(mark(scratch, site(relative, method, number, line, 'provider_field')))
        if line == '.end method':
            active = False
    path.write_text('\n'.join(result)+'\n', encoding='utf-8')

instrument(Path('smali/jpq.smali'), lambda s: ' a()Ljava/lang/Object;' in s,
           lambda s: s.strip().startswith('invoke-') or (s.strip().startswith('new-instance') and 'Ljpp;' in s), fields=True, entry=True)
instrument(Path('smali/kid.smali'), lambda s: ' b()Lpuf;' in s,
           lambda s: s.strip().startswith('invoke-'), entry=True)
instrument(Path('smali/hir.smali'), lambda s: ' J(Lpui;)Lisr;' in s,
           lambda s: 'invoke-' in s and ('->mb4c07af49db6252411e985c2793(' in s or 'Lput;->f(' in s), entry=True)
instrument(Path('smali_classes2/com/pairip/application/Application.smali'),
           lambda s: ' attachBaseContext(' in s or ' attach(' in s,
           lambda s: s.strip().startswith('invoke-'), entry=True)
instrument(Path('smali_classes2/com/google/android/apps/camera/legacy/app/app/CameraApp.smali'),
           lambda s: ' onCreate()V' in s,
           lambda s: 'invoke-direct' in s and 'Lcom/CameraLensesScan;-><init>()V' in s)
instrument(Path('smali_classes2/nki.smali'), lambda s: ' e()V' in s or ' f()V' in s or ' q(' in s,
           lambda s: False, entry=True)
path = a.output/'smali_classes2/mqt.smali'
text = (a.original_smali/'smali_classes2/mqt.smali').read_text(encoding='utf-8')
needle = '.method public final j(Ljava/lang/Enum;JLmqs;)V\n    .locals 4\n'
if text.count(needle) != 1:
    raise ValueError('Unexpected timing recorder')
path.write_text(text.replace(needle, needle+'\n    invoke-static {p0, p1, p2, p3}, Lx6810/gcam/StartupTimeline;->record(Lmqt;Ljava/lang/Enum;J)V\n'), encoding='utf-8')
dest = a.output/'smali_classes2/x6810/gcam/StartupTimeline.smali'
dest.parent.mkdir(parents=True, exist_ok=True)
shutil.copyfile(Path(__file__).with_name('StartupTimeline.smali'), dest)
(a.output/'sites.json').write_text(json.dumps(catalog, indent=2)+'\n', encoding='utf-8')
print('Prepared diagnostic sites:', len(catalog))
