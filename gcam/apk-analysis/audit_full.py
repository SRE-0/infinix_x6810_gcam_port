"""Index every decoded smali method/call and ELF dependency for startup review.

Read-only with respect to the APK and decoded tree. SQLite is a syntactic call
index, not a resolved runtime graph: virtual dispatch, reflection and JNI need
separate verification. No third-party Python dependencies.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import struct
import xml.etree.ElementTree as ET
import zipfile


def elf_info(data):
    if data[:6] != b'\x7fELF\x02\x01':
        return {'unsupported_elf': True}
    shoff = struct.unpack_from('<Q', data, 40)[0]
    entsize, count, names_index = struct.unpack_from('<HHH', data, 58)
    sections = [struct.unpack_from('<IIQQQQIIQQ', data, shoff+i*entsize)
                for i in range(count)]
    def blob(section):
        return data[section[4]:section[4]+section[5]]
    names = blob(sections[names_index])
    def string(table, offset):
        return table[offset:table.find(b'\0', offset)].decode(errors='replace')
    by_name = {string(names, s[0]): s for s in sections}
    needed, imports = [], []
    for name, section in by_name.items():
        if section[1] == 6:
            table = blob(sections[section[6]])
            values = blob(section)
            for offset in range(0, len(values), section[9] or 16):
                tag, value = struct.unpack_from('<qQ', values, offset)
                if tag == 1:
                    needed.append(string(table, value))
        if section[1] == 11:
            table = blob(sections[section[6]])
            values = blob(section)
            for offset in range(0, len(values), section[9] or 24):
                index, info, other, shndx, value, size = struct.unpack_from('<IBBHQQ', values, offset)
                if shndx == 0 and index:
                    imports.append(string(table, index))
    signals = {}
    for needle in (b'OpenCL', b'NNAPI', b'XNNPACK', b'Hexagon', b'libedgetpu',
                   b'portrait_segmenter', b'Gxp', b'clCreateProgram', b'vkCreate',
                   b'cache', b'Failed to updated cache'):
        occurrences = data.count(needle)
        if occurrences:
            signals[needle.decode()] = occurrences
    return {'needed': needed, 'imports': imports, 'string_signals': signals,
            'note': 'Strings/imports show potential code paths, not runtime use or compatibility.'}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('apk', type=Path)
    p.add_argument('decoded', type=Path)
    p.add_argument('output', type=Path)
    a = p.parse_args()
    a.output.mkdir(parents=True, exist_ok=True)
    db_path = a.output/'calls.sqlite'
    if db_path.exists():
        raise FileExistsError(db_path)
    db = sqlite3.connect(db_path)
    db.executescript('''
        CREATE TABLE methods(owner TEXT, signature TEXT, file TEXT, line INTEGER,
                             declaration TEXT);
        CREATE TABLE calls(owner TEXT, method TEXT, target TEXT, file TEXT,
                           line INTEGER, opcode TEXT);
        CREATE TABLE fields(owner TEXT, method TEXT, target TEXT, file TEXT,
                            line INTEGER, opcode TEXT);
        CREATE TABLE signals(owner TEXT, method TEXT, category TEXT, file TEXT,
                             line INTEGER, instruction TEXT);
    ''')
    patterns = {
        'ui': re.compile(r'LayoutInflater;->|ViewStub;->inflate|Choreographer;->|Landroid/view/View;->'),
        'blocking': re.compile(r'->(?:get|join|await|wait|sleep)\(|monitor-enter'),
        'worker': re.compile(r'Executor.*;->|Handler;->post|Thread;->start|HandlerThread;->'),
        'codec': re.compile(r'Landroid/media/(?:MediaCodec|MediaCodecList|CamcorderProfile);->'),
        'native_load': re.compile(r'->(?:loadLibrary|load)\(Ljava/lang/String;'),
        'disk': re.compile(r'Ljava/io/|->commit\(\)Z|Landroid/database/sqlite/'),
        'camera': re.compile(r'Landroid/hardware/camera2/.*;->'),
    }
    call_re = re.compile(r'^\s*(invoke-[\w/-]+).*?,\s*(L[^\s]+;->[^\s]+)')
    field_re = re.compile(r'^\s*([is][gp]et[\w/-]*|[is]put[\w/-]*).*?,\s*(L[^\s]+;->[^\s]+)')
    counts = Counter()
    for path in sorted(a.decoded.glob('smali*/**/*.smali')):
        relative = path.relative_to(a.decoded).as_posix()
        owner, method = '', ''
        calls, fields, signals, methods = [], [], [], []
        for lineno, line in enumerate(path.read_text(encoding='utf-8').splitlines(), 1):
            if line.startswith('.class '):
                owner = line.split()[-1]
            elif line.startswith('.method '):
                method = line.split()[-1]
                methods.append((owner, method, relative, lineno, line))
            elif line.startswith('.end method'):
                method = ''
            if not method:
                continue
            match = call_re.match(line)
            if match:
                calls.append((owner, method, match[2], relative, lineno, match[1]))
            match = field_re.match(line)
            if match:
                fields.append((owner, method, match[2], relative, lineno, match[1]))
            for category, pattern in patterns.items():
                if pattern.search(line):
                    signals.append((owner, method, category, relative, lineno, line.strip()))
                    counts[category] += 1
        db.executemany('INSERT INTO methods VALUES(?,?,?,?,?)', methods)
        db.executemany('INSERT INTO calls VALUES(?,?,?,?,?,?)', calls)
        db.executemany('INSERT INTO fields VALUES(?,?,?,?,?,?)', fields)
        db.executemany('INSERT INTO signals VALUES(?,?,?,?,?,?)', signals)
        counts['classes'] += 1
        counts['methods'] += len(methods)
        counts['calls'] += len(calls)
        counts['fields'] += len(fields)
    db.executescript('''
        CREATE INDEX calls_target ON calls(target);
        CREATE INDEX calls_source ON calls(owner,method);
        CREATE INDEX fields_target ON fields(target);
        CREATE INDEX signals_category ON signals(category);
    ''')
    db.commit()
    db.close()
    ns = '{http://schemas.android.com/apk/res/android}'
    manifest = ET.parse(a.decoded/'AndroidManifest.xml').getroot()
    app = manifest.find('application')
    components = []
    for node in app:
        if node.tag in ('provider', 'service', 'receiver', 'activity', 'activity-alias'):
            components.append({'type': node.tag, **{k.removeprefix(ns): v for k,v in node.attrib.items()},
                               'metadata': [{k.removeprefix(ns): v for k,v in m.attrib.items()}
                                            for m in node.findall('meta-data')]})
    native, dex = {}, {}
    with zipfile.ZipFile(a.apk) as z:
        for entry in z.infolist():
            if entry.filename.endswith('.dex'):
                data = z.read(entry)
                dex[entry.filename] = {'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest(),
                    'method_ids': struct.unpack_from('<I', data, 88)[0],
                    'class_defs': struct.unpack_from('<I', data, 96)[0]}
            elif entry.filename.startswith('lib/') and entry.filename.endswith('.so'):
                data = z.read(entry)
                native[entry.filename] = {'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest(),
                                         **elf_info(data)}
    result = {'apk_sha256': hashlib.file_digest(a.apk.open('rb'), 'sha256').hexdigest(),
              'counts': dict(counts), 'dex': dex, 'components': components, 'native': native,
              'limitations': ['Syntactic coverage is not an exhaustive semantic audit.',
                              'Interface dispatch, reflection, encrypted assets and JNI are not resolved.',
                              'Blocking signals include nonblocking get methods; inspect manually.',
                              'Native binaries are inventoried, not fully decompiled into source.']}
    (a.output/'audit.json').write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({'counts': dict(counts), 'dex': dex, 'native_libraries': len(native),
                      'components': len(components)}, indent=2))


if __name__ == '__main__':
    main()
