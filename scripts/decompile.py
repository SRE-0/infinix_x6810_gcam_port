"""Decode a locally held APK into ignored storage; never publish decoded output."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apk', type=Path, default=ROOT / 'gcam/apatch-startup/payload/MGC_9.7.047_V32_MGC.apk')
    parser.add_argument('--apktool-jar', type=Path)
    parser.add_argument('--jadx', type=Path, help='Optional JADX executable for Java source inspection')
    parser.add_argument('--output', type=Path)
    parser.add_argument('--plan', action='store_true', help='Print commands without creating decoded files')
    args = parser.parse_args()
    apk = args.apk.resolve(strict=True)
    with apk.open('rb') as stream:
        digest = hashlib.file_digest(stream, 'sha256').hexdigest()
    local = (ROOT / '.local-private').resolve()
    if not local.is_relative_to(ROOT.resolve()):
        parser.error('Local storage must remain inside this repository')
    output = (args.output or local / 'decompilation' / digest).resolve()
    if output == local or not output.is_relative_to(local):
        parser.error('Output must be a child of this repository\'s ignored .local-private directory')
    if output.exists():
        parser.error('Output already exists; choose a new local directory (no automatic overwrite)')
    if args.apktool_jar:
        tool = args.apktool_jar.resolve(strict=True)
        commands = [['java', '-jar', str(tool), 'd', str(apk), '-o', str(output / 'apktool')]]
    else:
        executable = shutil.which('apktool')
        if not executable:
            parser.error('Install Apktool separately or provide --apktool-jar')
        commands = [[executable, 'd', str(apk), '-o', str(output / 'apktool')]]
    if args.jadx:
        commands.append([str(args.jadx.resolve(strict=True)), '-d', str(output / 'jadx'), str(apk)])
    plan = {'apk': str(apk), 'sha256': digest, 'output': str(output), 'commands': commands}
    print(json.dumps(plan, indent=2))
    if args.plan:
        return
    output.mkdir(parents=True)
    (output / 'provenance.json').write_text(json.dumps(plan, indent=2)+'\n', encoding='utf-8')
    for command in commands:
        subprocess.run(command, check=True)

if __name__ == '__main__':
    main()
