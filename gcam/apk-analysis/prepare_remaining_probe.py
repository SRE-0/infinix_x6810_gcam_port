"""Isolated Java diagnostics, preserving registers and adjacent move-result.

All added call sites invoke static no-argument methods: .locals and parameter
registers stay unchanged. Cache paths are logged and returned unchanged.
Input is the retained CRC main tree and lazy-options timing secondary tree.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('main', type=Path)
p.add_argument('secondary', type=Path)
p.add_argument('output', type=Path)
a = p.parse_args()
if a.output.exists():
    raise FileExistsError(a.output)
for source in (a.main, a.secondary):
    if source.resolve() == a.output.resolve() or source.resolve() in a.output.resolve().parents:
        raise ValueError('Diagnostic copy must be isolated')
shutil.copytree(a.main, a.output/'smali')
shutil.copytree(a.secondary, a.output/'smali_classes2')
owner = 'Lx6810/gcam/RemainingProbe;'
helper = ['.class public final '+owner, '.super Ljava/lang/Object;', '''
.method private static mark(Ljava/lang/String;)V
    .locals 4
    invoke-static {}, Landroid/os/SystemClock;->elapsedRealtimeNanos()J
    move-result-wide v0
    new-instance v2, Ljava/lang/StringBuilder;
    invoke-direct {v2}, Ljava/lang/StringBuilder;-><init>()V
    invoke-virtual {v2, p0}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    const-string v3, " now_ns="
    invoke-virtual {v2, v3}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    invoke-virtual {v2, v0, v1}, Ljava/lang/StringBuilder;->append(J)Ljava/lang/StringBuilder;
    invoke-virtual {v2}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;
    move-result-object v0
    const-string v1, "X6810_REMAINING"
    invoke-static {v1, v0}, Landroid/util/Log;->i(Ljava/lang/String;Ljava/lang/String;)I
    return-void
.end method
''']
sites = []

def marker(index, phase):
    name = f's{index}_{phase}'
    helper.append(f'''
.method public static {name}()V
    .locals 1
    const-string v0, "site={index} phase={phase}"
    invoke-static {{v0}}, {owner}->mark(Ljava/lang/String;)V
    return-void
.end method
''')
    return f'    invoke-static {{}}, {owner}->{name}()V'

def instrument(relative, method_selector, call_selector):
    path = a.output/relative
    lines = path.read_text(encoding='utf-8').splitlines()
    out = []
    active = False
    for number, line in enumerate(lines):
        if line.startswith('.method '):
            method = line
            active = method_selector(method)
        if active and line.strip().startswith('invoke-') and call_selector(line):
            index = len(sites)+1
            sites.append(dict(id=index, file=relative, method=method, line=number+1,
                              instruction=line.strip()))
            out.append(marker(index, 'begin'))
            out.append(line)
            next_line = lines[number+1].strip()
            # Canonical files place a blank then move-result. Find next instruction.
            following = next((x.strip() for x in lines[number+1:] if x.strip() and
                              not x.strip().startswith(('#', '.line', '.local'))), '')
            if following.startswith('move-result'):
                pending = marker(index, 'end')
            else:
                out.append(marker(index, 'end'))
                pending = None
            continue
        out.append(line)
        if active and line.strip().startswith('move-result') and pending:
            out.append(pending)
            pending = None
        if line == '.end method':
            active = False
        if line.startswith('.method '):
            pending = None
    path.write_text('\n'.join(out)+'\n', encoding='utf-8')

instrument('smali_classes2/nsu.smali', lambda m: ' a()V' in m, lambda _: True)
instrument('smali_classes2/lqv.smali', lambda m: ' b()V' in m,
           lambda s: '->initSegmenter(' in s or '->dummyImageProducesReasonableMask(' in s)
instrument('smali_classes2/lrl.smali', lambda m: ' call()Ljava/lang/Object;' in m,
           lambda s: 'NativePortraitPreviewProcessor;->create(' in s)
instrument('smali/iuv.smali', lambda m: ' b()V' in m,
           lambda s: 'NativeFaceToPortraitSegmenter;->initSegmenterNative(' in s)

for relative, name in (('smali_classes2/lqv.smali','cacheLqv'),
                       ('smali/iuv.smali','cacheIuv'),
                       ('smali/fgj.smali','cacheGcam')):
    path = a.output/relative
    text = path.read_text(encoding='utf-8')
    pattern = r'    invoke-virtual \{(\w+)\}, Ljava/io/File;->getAbsolutePath\(\)Ljava/lang/String;'
    matches = list(re.finditer(pattern, text))
    if len(matches) != 1:
        raise ValueError('Expected a single cache path site: '+relative)
    text = re.sub(pattern, lambda m: f'    invoke-static {{{m[1]}}}, {owner}->{name}(Ljava/io/File;)Ljava/lang/String;', text)
    path.write_text(text, encoding='utf-8')
    helper.append(f'''
.method public static {name}(Ljava/io/File;)Ljava/lang/String;
    .locals 2
    invoke-virtual {{p0}}, Ljava/io/File;->getAbsolutePath()Ljava/lang/String;
    move-result-object v0
    const-string v1, "{name} path="
    invoke-virtual {{v1, v0}}, Ljava/lang/String;->concat(Ljava/lang/String;)Ljava/lang/String;
    move-result-object v1
    invoke-static {{v1}}, {owner}->mark(Ljava/lang/String;)V
    return-object v0
.end method
''')
dest = a.output/'smali_classes2/x6810/gcam/RemainingProbe.smali'
dest.parent.mkdir(parents=True, exist_ok=True)
dest.write_text('\n'.join(helper)+'\n', encoding='utf-8')
(a.output/'sites.json').write_text(json.dumps(sites, indent=2)+'\n')
print('Prepared',len(sites),'paired Java sites; no cache path changes')
