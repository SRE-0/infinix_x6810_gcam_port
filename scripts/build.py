"""Build the independent GCam system module from an explicitly supplied APK."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]

def sha(path):
    with path.open('rb') as source:
        return hashlib.file_digest(source, 'sha256').hexdigest()

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apk', type=Path, required=True, help='Original signed BSG 9.7 V32 APK')
    parser.add_argument('--output', type=Path, default=ROOT / 'dist/releases')
    args = parser.parse_args()
    if not args.apk.is_file():
        raise FileNotFoundError(args.apk)
    args.output.mkdir(parents=True, exist_ok=True)
    module = ROOT / 'gcam/apatch-startup'
    metadata = dict(line.split('=', 1) for line in (module / 'module.prop').read_text().splitlines() if '=' in line)
    output = args.output / f'x6810-gcam-system-{metadata["version"]}.zip'
    subprocess.run([sys.executable, str(module / 'build.py'), str(args.apk.resolve()), str(output.resolve()),
                    '--native', str(module / 'payload/libgcastartup-cache.so')], check=True)
    overlay = args.output / 'x6810-gcam-bsg-v18-recommended.xml'
    shutil.copyfile(ROOT / 'profiles' / overlay.name, overlay)
    records = [{'file': p.name, 'sha256': sha(p)} for p in (output, overlay)]
    (args.output / 'SHA256SUMS.txt').write_text(''.join(f'{r["sha256"]}  {r["file"]}\n' for r in records), encoding='ascii', newline='\n')
    (args.output / 'releases.json').write_text(json.dumps(records, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(records, indent=2))

if __name__ == '__main__':
    main()
