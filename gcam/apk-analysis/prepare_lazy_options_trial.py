"""Prepare isolated cache+scan6 trials with lazy PHOTO options rows.

Keep the panel shell and callbacks eagerly wired. Only suppress initial row
rebuilding for a closed bottom sheet in PHOTO. Preserve dirty state and update
feature/controller state through the existing case 10. First opening builds
synchronously before displaying; subsequent updates retain original behavior.
"""
import argparse
from pathlib import Path
import shutil

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('cache_main', type=Path)
p.add_argument('secondary', type=Path)
p.add_argument('output', type=Path)
p.add_argument('--reuse-copy', action='store_true', help='Reset only patch sites from isolated baseline')
a = p.parse_args()
if a.output.exists() and not a.reuse_copy:
    raise FileExistsError(a.output)
for source in (a.cache_main, a.secondary):
    if source.resolve() == a.output.resolve() or source.resolve() in a.output.resolve().parents:
        raise ValueError('Output must be isolated')
if not a.reuse_copy:
    for variant in ('baseline', 'lazy-options'):
        dest = a.output/variant
        shutil.copytree(a.cache_main, dest/'smali')
        shutil.copytree(a.secondary, dest/'smali_classes2')

dest = a.output/'lazy-options'
for relative in ('smali/kzh.smali', 'smali_classes2/leb.smali', 'smali_classes2/ldz.smali'):
    shutil.copyfile(a.output/'baseline'/relative, dest/relative)
path = dest/'smali/kzh.smali'
text = path.read_text(encoding='utf-8')
decl = '.method public final run()V'
if text.count(decl) != 1:
    raise ValueError('Unexpected kzh.run')
text = text.replace(decl, '.method private final x6810OriginalRun()V')
text += '''
.method public final run()V
    .locals 3
    iget v0, p0, Lkzh;->b:I
    const/16 v1, 0x9
    if-ne v0, v1, :original
    iget-object v0, p0, Lkzh;->a:Ljava/lang/Object;
    check-cast v0, Lleb;
    iget-object v1, v0, Lleb;->r:Lcom/google/android/apps/camera/optionsbar/view/OptionsMenuContainer;
    if-eqz v1, :original
    iget-boolean v1, v0, Lleb;->x6810OptionsOpened:Z
    if-nez v1, :original
    invoke-virtual {v0}, Lleb;->d()Lntq;
    move-result-object v1
    sget-object v2, Lntq;->b:Lntq;
    if-ne v1, v2, :original
    invoke-virtual {v0}, Lleb;->t()Z
    move-result v1
    if-nez v1, :original
    # Existing state-only update; no widgets. Leave x/y dirty for first open.
    new-instance v1, Lkzh;
    const/16 v2, 0xa
    invoke-direct {v1, v0, v2}, Lkzh;-><init>(Ljava/lang/Object;I)V
    invoke-virtual {v1}, Lkzh;->run()V
    return-void
    :original
    invoke-direct {p0}, Lkzh;->x6810OriginalRun()V
    return-void
.end method
'''
path.write_text(text, encoding='utf-8')

path = dest/'smali_classes2/leb.smali'
text = path.read_text(encoding='utf-8')
anchor = '# instance fields\n'
if text.count(anchor) != 1:
    raise ValueError('Unexpected leb field section')
text = text.replace(anchor, anchor+'\n.field public x6810OptionsOpened:Z\n')
start = text.index('.method public final y(ILlem;)V')
end = text.index('.end method', start)
method = text[start:end]
call = '    invoke-virtual {p0}, Lleb;->p()V'
if method.count(call) != 1:
    raise ValueError('Unexpected first-open build site')
# v0 is live in the opaque method: avoid a scratch register by calling a tiny
# instance helper which sets the flag and invokes the existing dirty refresh.
method = method.replace(call, '    invoke-virtual {p0}, Lleb;->x6810OpenOptions()V')
text = text[:start]+method+text[end:]
text += '''
.method public final x6810OpenOptions()V
    .locals 1
    const/4 v0, 0x1
    iput-boolean v0, p0, Lleb;->x6810OptionsOpened:Z
    invoke-virtual {p0}, Lleb;->p()V
    return-void
.end method
'''
path.write_text(text, encoding='utf-8')

# BottomSheetBehavior can also expand through dragging/accessibility. Preserve
# the original callback, but ensure rows exist for those opening paths too.
path = dest/'smali_classes2/ldz.smali'
text = path.read_text(encoding='utf-8')
decl = '.method public final b(Landroid/view/View;I)V'
if text.count(decl) != 1:
    raise ValueError('Unexpected bottom sheet callback')
text = text.replace(decl, '.method private final x6810OriginalStateChanged(Landroid/view/View;I)V')
text += '''
.method public final b(Landroid/view/View;I)V
    .locals 2
    const/4 v0, 0x3
    if-ne p2, v0, :original
    iget-object v0, p0, Lldz;->a:Lleb;
    iget-boolean v1, v0, Lleb;->x6810OptionsOpened:Z
    if-nez v1, :original
    invoke-virtual {v0}, Lleb;->x6810OpenOptions()V
    :original
    invoke-direct {p0, p1, p2}, Lldz;->x6810OriginalStateChanged(Landroid/view/View;I)V
    return-void
.end method
'''
path.write_text(text, encoding='utf-8')
print('Prepared baseline and lazy PHOTO row trial; all opening paths guarded')
