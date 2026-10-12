"""Prepare the optimized APK's secondary DEX without diagnostic event logging."""
from helper_templates import helper_path
import argparse
from pathlib import Path
import shutil

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('original', type=Path)
p.add_argument('output', type=Path)
a = p.parse_args()
if a.output.resolve() == a.original.resolve() or a.original.resolve() in a.output.resolve().parents:
    raise ValueError('Output must be isolated from original smali')
shutil.copytree(a.original/'smali_classes2', a.output)
dest = a.output/'x6810/gcam/ProfileScope.smali'
dest.parent.mkdir(parents=True, exist_ok=True)
shutil.copyfile(helper_path('ProfileScope.smali'), dest)
print('Prepared original secondary DEX plus only the scoped cache helper')
