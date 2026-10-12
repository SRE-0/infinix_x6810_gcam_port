"""Extend the prepared class worker with background-only font cache warming."""
import argparse
from pathlib import Path

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('directory', type=Path)
a = p.parse_args()
path = a.directory/'smali_classes2/x6810/gcam/StartupWorker.smali'
text = path.read_text()
if '.field private context:' in text: raise ValueError('Font trial already prepared')
text = text.replace('.field private loaded:I', '.field private loaded:I\n.field private context:Landroid/content/Context;')
needle = '    invoke-direct {v1, v0}, Lx6810/gcam/StartupWorker;-><init>(Ljava/lang/ClassLoader;)V'
if text.count(needle) != 1: raise ValueError('Unexpected worker constructor')
text = text.replace(needle, needle + '\n    iput-object p0, v1, Lx6810/gcam/StartupWorker;->context:Landroid/content/Context;')
needle = '    const-string v3, "kkh"'
fonts = '\n'.join('    const v3, '+resource+'\n    invoke-direct {p0, v3}, Lx6810/gcam/StartupWorker;->font(I)V' for resource in ['0x7f09000e', '0x7f09001a', '0x7f09001e'])
text = text.replace(needle, fonts + '\n' + needle)
text += '''
.method private font(I)V
    .locals 7
    :font_start
    iget-object v0, p0, Lx6810/gcam/StartupWorker;->context:Landroid/content/Context;
    move v1, p1
    new-instance v2, Landroid/util/TypedValue;
    invoke-direct {v2}, Landroid/util/TypedValue;-><init>()V
    const/4 v3, 0x0
    const/4 v4, 0x0
    const/4 v5, 0x0
    const/4 v6, 0x0
    invoke-static/range {v0 .. v6}, Ldwp;->b(Landroid/content/Context;ILandroid/util/TypedValue;ILdwo;ZZ)Landroid/graphics/Typeface;
    const-string v0, "X6810_THREADING"
    const-string v1, "font preload complete"
    invoke-static {v0, v1}, Landroid/util/Log;->i(Ljava/lang/String;Ljava/lang/String;)I
    :font_end
    .catch Ljava/lang/Throwable; {:font_start .. :font_end} :font_failed
    return-void
    :font_failed
    move-exception v0
    const-string v1, "X6810_THREADING"
    const-string v2, "font preload failed; original UI loader remains active"
    invoke-static {v1, v2, v0}, Landroid/util/Log;->w(Ljava/lang/String;Ljava/lang/String;Ljava/lang/Throwable;)I
    return-void
.end method
'''
path.write_text(text)
print('Prepared three font resources on worker; no UI callback or View access')
