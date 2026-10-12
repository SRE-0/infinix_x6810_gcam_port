"""Read-only inventory of the installed GCam APK and decompiler outputs."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

p = argparse.ArgumentParser()
p.add_argument("apk", type=Path)
p.add_argument("analysis", type=Path)
a = p.parse_args()
digest = hashlib.file_digest(a.apk.open("rb"), "sha256").hexdigest()
with zipfile.ZipFile(a.apk) as z:
    files = z.infolist()
    selected = [i for i in files if i.filename.endswith(".dex") or
                (i.filename.startswith("lib/") and i.filename.endswith(".so"))]
    entries = [{"name": i.filename, "size": i.file_size,
                "compressed_size": i.compress_size, "compression": i.compress_type}
               for i in selected]
result = {"apk": str(a.apk), "sha256": digest, "bytes": a.apk.stat().st_size,
          "zip_entries": len(files), "code": entries,
          "java_files": sum(1 for _ in (a.analysis / "jadx/sources").rglob("*.java")),
          "smali_files": sum(1 for _ in (a.analysis / "apktool").rglob("*.smali"))}
(a.analysis / "inventory.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
print(json.dumps({k: v for k, v in result.items() if k != "code"}, indent=2))
