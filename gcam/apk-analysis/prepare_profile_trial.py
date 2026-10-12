"""Prepare isolated baseline/optimization DEX trees with identical event logging.

The optimization caches profile queries only within one hir.J call. No UI or
HAL work is moved to another thread. Keep original extraction untouched.
"""
from helper_templates import helper_path
import argparse
from pathlib import Path
import shutil

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('original', type=Path)
p.add_argument('output', type=Path)
a = p.parse_args()
if a.output.resolve() == a.original.resolve() or a.original.resolve() in a.output.resolve().parents:
    raise ValueError('Use a separate output directory')
a.output.mkdir(parents=True, exist_ok=False)
for name in ('baseline', 'profile-cache'):
    out = a.output/name
    shutil.copytree(a.original/'smali', out/'smali')
# Both APKs share exactly the same secondary DEX and logging overhead.
secondary = a.output/'shared/smali_classes2'
shutil.copytree(a.original/'smali_classes2', secondary)
helper = secondary/'x6810/gcam'
helper.mkdir(parents=True, exist_ok=True)
for name in ('StartupTimeline.smali', 'ProfileScope.smali'):
    shutil.copyfile(helper_path(name), helper/name)
recorder = secondary/'mqt.smali'
text = recorder.read_text(encoding='utf-8')
needle = '.method public final j(Ljava/lang/Enum;JLmqs;)V\n    .locals 4\n'
if text.count(needle) != 1:
    raise ValueError('Unexpected event recorder')
recorder.write_text(text.replace(needle, needle+'\n    invoke-static {p0, p1, p2, p3}, Lx6810/gcam/StartupTimeline;->record(Lmqt;Ljava/lang/Enum;J)V\n'), encoding='utf-8')
path = a.output/'profile-cache/smali/hir.smali'
text = path.read_text(encoding='utf-8')
old = '.method public final J(Lpui;)Lisr;'
if text.count(old) != 1:
    raise ValueError('Unexpected hir.J declaration')
# Verify these calls are private to the six-list builder, which uses the same
# camera ID during one J invocation. Do not cache elsewhere in the process.
start = text.index('.method private final mb4c07af49db6252411e985c2793(')
end = text.index('.end method', start)
method = text[start:end]
has = 'Landroid/media/CamcorderProfile;->hasProfile(II)Z'
profile = 'Losh;->aW(Lpui;Lpgf;)Lpgh;'
if method.count(has) != 1 or method.count(profile) != 1:
    raise ValueError('Unexpected profile query sites')
method = method.replace(has, 'Lx6810/gcam/ProfileScope;->has(II)Z').replace(profile, 'Lx6810/gcam/ProfileScope;->profile(Lpui;Lpgf;)Lpgh;')
text = text[:start]+method+text[end:]
text = text.replace(old, '.method private final x6810BuildProfiles(Lpui;)Lisr;')
wrapper = '''
.method public final J(Lpui;)Lisr;
    .locals 1
    invoke-static {}, Lx6810/gcam/ProfileScope;->begin()V
    :x6810_try_start
    invoke-direct {p0, p1}, Lhir;->x6810BuildProfiles(Lpui;)Lisr;
    move-result-object v0
    :x6810_try_end
    .catchall {:x6810_try_start .. :x6810_try_end} :x6810_failure
    invoke-static {}, Lx6810/gcam/ProfileScope;->end()V
    return-object v0
    :x6810_failure
    move-exception v0
    invoke-static {}, Lx6810/gcam/ProfileScope;->end()V
    throw v0
.end method
'''
path.write_text(text+wrapper, encoding='utf-8')
print('Prepared baseline, profile-cache, and shared timing/helper DEX trees')
