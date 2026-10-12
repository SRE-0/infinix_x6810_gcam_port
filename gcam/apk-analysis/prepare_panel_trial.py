"""Defer PHOTO panel-only value subscriptions and tabs, retaining camera state wiring.

Extract the original tab CFG without rewriting its instructions. Keep the shell,
minibar and ler.m camera/state subscriptions eager. First touch/drag/accessibility
opening synchronously prepares the pending UI work on main before row refresh.
"""
import argparse
import json
from pathlib import Path
import re
import shutil

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('secondary', type=Path)
p.add_argument('output', type=Path)
a = p.parse_args()
if a.output.exists():
    raise FileExistsError(a.output)
if a.secondary.resolve() == a.output.resolve() or a.secondary.resolve() in a.output.resolve().parents:
    raise ValueError('Output must be isolated')
shutil.copytree(a.secondary, a.output)
path = a.output/'nsu.smali'
text = path.read_text(encoding='utf-8')
start = text.index('.method public final a()V')
end = text.index('.end method', start)
method = text[start:end]
lines = [x.strip() for x in method.splitlines() if x.strip() and x.strip() != 'nop'
         and not x.strip().startswith('#')]
labels = {x:i for i,x in enumerate(lines) if x.startswith(':')}
entry, exit_label = ':cond_17', ':goto_1a9'
visited, todo = set(), [labels[entry]]
while todo:
    i = todo.pop()
    if i == labels[exit_label] or i in visited:
        continue
    visited.add(i)
    instruction = lines[i]
    if instruction.startswith('goto'):
        todo.append(labels[instruction.split()[-1]])
    elif instruction.startswith('if-'):
        todo.extend((i+1, labels[instruction.split()[-1]]))
    elif instruction.startswith(('return', 'packed-switch', 'sparse-switch')):
        raise ValueError('Unexpected tab region instruction')
    else:
        todo.append(i+1)
body = '\n'.join(lines[i] for i in sorted(visited))
if len(visited) != 534 or re.search(r'\bp0\b', body):
    raise ValueError('Unexpected tab CFG')
if body.count('Lcom/google/android/material/tabs/TabLayout;->e()Lruu;') != 2:
    raise ValueError('Expected two original tabs')
# Original entry live-ins: leb=v2, -1=v3, true=v4, zero=v5, margins=2=v6,
# null=v11. These constants are unchanged across the extracted region.
helper = '''.class public final Lx6810/gcam/PanelTabs;
.super Ljava/lang/Object;
.method public static build(Lleb;)V
    .locals 15
    invoke-static {}, Lpdh;->a()V
    move-object v2, p0
    const/4 v3, -0x1
    const/4 v4, 0x1
    const/4 v5, 0x0
    const/4 v6, 0x2
    const/4 v11, 0x0
    goto/32 :cond_17
'''+body+'\n'+exit_label+'\n    return-void\n.end method\n'
dest = a.output/'x6810/gcam/PanelTabs.smali'
dest.parent.mkdir(parents=True, exist_ok=True)
dest.write_text(helper, encoding='utf-8')
anchor = '    :cond_17\n    goto/32 :goto_68'
if method.count(anchor) != 1:
    # Canonical smali has blank lines between label and goto.
    pattern = r'    :cond_17\s+goto/32 :goto_68'
    if len(re.findall(pattern, method)) != 1:
        raise ValueError('Unexpected tab entry')
    method = re.sub(pattern, '    :cond_17\n    invoke-virtual {v2}, Lleb;->x6810StageTabs()V\n    goto/32 :goto_1a9', method)
else:
    method = method.replace(anchor, '    :cond_17\n    invoke-virtual {v2}, Lleb;->x6810StageTabs()V\n    goto/32 :goto_1a9')
# Only case 13 is UI value display; case 14 calls ler.m and remains eager.
pattern = r'(:goto_11c\s+)invoke-static \{v0, v3\}, Lj\$/util/Collection\$-EL;->forEach\(Ljava/util/Collection;Ljava/util/function/Consumer;\)V'
if len(re.findall(pattern, method)) != 1:
    raise ValueError('Unexpected case-13 subscription site')
method = re.sub(pattern, r'\1invoke-virtual {v2, v0, v3}, Lleb;->x6810StageValues(Ljava/util/Collection;Ljava/util/function/Consumer;)V', method)
path.write_text(text[:start]+method+text[end:], encoding='utf-8')

path = a.output/'leb.smali'
text = path.read_text(encoding='utf-8')
text = text.replace('# instance fields\n', '''# instance fields
.field private x6810PendingValues:Ljava/util/Collection;
.field private x6810PendingConsumer:Ljava/util/function/Consumer;
.field private x6810TabsReady:Z
''', 1)
anchor = '    iput-boolean v0, p0, Lleb;->x6810OptionsOpened:Z'
if text.count(anchor) != 1:
    raise ValueError('Expected existing first-open helper')
text = text.replace(anchor, anchor+'\n    invoke-virtual {p0}, Lleb;->x6810PreparePanel()V', 1)
text += '''
.method private final x6810DeferPanel()Z
    .locals 2
    iget-boolean v0, p0, Lleb;->x6810OptionsOpened:Z
    if-nez v0, :eager
    invoke-virtual {p0}, Lleb;->d()Lntq;
    move-result-object v0
    sget-object v1, Lntq;->b:Lntq;
    if-ne v0, v1, :eager
    invoke-virtual {p0}, Lleb;->t()Z
    move-result v0
    if-nez v0, :eager
    const/4 v0, 0x1
    return v0
    :eager
    const/4 v0, 0x0
    return v0
.end method

.method public final x6810StageValues(Ljava/util/Collection;Ljava/util/function/Consumer;)V
    .locals 1
    invoke-direct {p0}, Lleb;->x6810DeferPanel()Z
    move-result v0
    if-eqz v0, :eager
    iput-object p1, p0, Lleb;->x6810PendingValues:Ljava/util/Collection;
    iput-object p2, p0, Lleb;->x6810PendingConsumer:Ljava/util/function/Consumer;
    return-void
    :eager
    invoke-static {p1, p2}, Lj$/util/Collection$-EL;->forEach(Ljava/util/Collection;Ljava/util/function/Consumer;)V
    return-void
.end method

.method public final x6810StageTabs()V
    .locals 1
    invoke-direct {p0}, Lleb;->x6810DeferPanel()Z
    move-result v0
    if-nez v0, :done
    invoke-virtual {p0}, Lleb;->x6810PreparePanel()V
    :done
    return-void
.end method

.method public final x6810PreparePanel()V
    .locals 3
    invoke-static {}, Lpdh;->a()V
    iget-object v0, p0, Lleb;->x6810PendingValues:Ljava/util/Collection;
    if-eqz v0, :tabs
    iget-object v1, p0, Lleb;->x6810PendingConsumer:Ljava/util/function/Consumer;
    const/4 v2, 0x0
    iput-object v2, p0, Lleb;->x6810PendingValues:Ljava/util/Collection;
    iput-object v2, p0, Lleb;->x6810PendingConsumer:Ljava/util/function/Consumer;
    invoke-static {v0, v1}, Lj$/util/Collection$-EL;->forEach(Ljava/util/Collection;Ljava/util/function/Consumer;)V
    :tabs
    iget-boolean v0, p0, Lleb;->A:Z
    if-eqz v0, :done
    iget-boolean v0, p0, Lleb;->x6810TabsReady:Z
    if-nez v0, :done
    invoke-static {p0}, Lx6810/gcam/PanelTabs;->build(Lleb;)V
    const/4 v0, 0x1
    iput-boolean v0, p0, Lleb;->x6810TabsReady:Z
    :done
    return-void
.end method
'''
path.write_text(text, encoding='utf-8')
(a.output.parent/(a.output.name+'-scope.json')).write_text(json.dumps({
    'changed_classes':['nsu','leb'], 'added_classes':['x6810/gcam/PanelTabs'],
    'tab_cfg_lines':len(visited), 'eager':['shell','minibar','ler.m','camera/lifecycle'],
    'deferred':['case13 UI value subscriptions','tab adapter and tab creation'],
    'opening_guard':'existing x6810OpenOptions on touch/expanded callback',
}, indent=2)+'\n')
print('Prepared panel trial: original tab CFG and UI value subscriptions deferred')
