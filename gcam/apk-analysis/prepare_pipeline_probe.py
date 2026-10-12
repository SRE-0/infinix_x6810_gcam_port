"""Temporary paired codec/ML diagnostics, with original registers unchanged."""
import argparse
import json
from pathlib import Path
import shutil

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('main', type=Path)
p.add_argument('secondary', type=Path)
p.add_argument('output', type=Path)
p.add_argument('--reuse-copy', action='store_true', help='Reset selected classes in an isolated existing copy')
a = p.parse_args()
if a.output.exists() and not a.reuse_copy:
    raise FileExistsError(a.output)
for source in (a.main, a.secondary):
    if source.resolve() == a.output.resolve() or source.resolve() in a.output.resolve().parents:
        raise ValueError('Output must be isolated')
if not a.reuse_copy:
    shutil.copytree(a.main, a.output/'smali')
    shutil.copytree(a.secondary, a.output/'smali_classes2')
owner = 'Lx6810/gcam/PipelineProbe;'
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
    const-string v1, "X6810_PIPELINE"
    invoke-static {v1, v0}, Landroid/util/Log;->i(Ljava/lang/String;Ljava/lang/String;)I
    return-void
.end method
''']
sites = []

def mark(index, phase):
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

targets = {
    'smali_classes2/osh.smali':['MediaCodec;->createEncoderByType'],
    'smali/jay.smali':['MediaCodec;->createEncoderByType'],
    'smali/jbe.smali':['MediaCodec;->createEncoderByType'],
    'smali/jbv.smali':['MediaCodec;->createEncoderByType'],
    'smali/iuv.smali':['NativeFaceToPortraitSegmenter;->initSegmenterNative'],
    'smali/kob.smali':['MediaCodec;->createEncoderByType'],
    'smali/koa.smali':['MediaCodec;->createEncoderByType'],
    'smali_classes2/qiv.smali':['MediaCodec;->createEncoderByType'],
    'smali_classes2/phr.smali':['Losh;->aY'],
    'smali_classes2/lqv.smali':['->initSegmenter('],
    'smali_classes2/lrl.smali':['NativePortraitPreviewProcessor;->create'],
    'smali_classes2/nsu.smali':['->x6810StageValues','->x6810StageTabs'],
    'smali_classes2/leb.smali':['->x6810PreparePanel','PanelTabs;->build'],
}
for relative, tokens in targets.items():
    path = a.output/relative
    if a.reuse_copy:
        source = (a.main if relative.startswith('smali/') else a.secondary)/Path(relative).name
        shutil.copyfile(source, path)
    lines = path.read_text(encoding='utf-8').splitlines()
    out, pending = [], None
    for number, line in enumerate(lines):
        if line.startswith('.method '):
            method = line
        if line.strip().startswith('invoke-') and any(t in line for t in tokens):
            index = len(sites)+1
            sites.append(dict(id=index,file=relative,method=method,instruction=line.strip()))
            out.extend((mark(index,'begin'),line))
            following = next((x.strip() for x in lines[number+1:] if x.strip()
                              and not x.strip().startswith(('#','.line','.local'))),'')
            if following.startswith('move-result'):
                pending = mark(index,'end')
            else:
                out.append(mark(index,'end'))
            continue
        out.append(line)
        if pending and line.strip().startswith('move-result'):
            out.append(pending)
            pending = None
    if pending:
        raise ValueError('Unpaired result')
    path.write_text('\n'.join(out)+'\n',encoding='utf-8')
dest = a.output/'smali_classes2/x6810/gcam/PipelineProbe.smali'
dest.parent.mkdir(parents=True,exist_ok=True)
dest.write_text('\n'.join(helper)+'\n',encoding='utf-8')
(a.output/'sites.json').write_text(json.dumps(sites,indent=2)+'\n')
print('Prepared',len(sites),'codec, ML and first-open sites')
