"""Scope CRC normalization to the first transformed ELF extraction in Application.b.

Keep ordinary bc(File), the secondary ZIP extraction and all loader behavior intact.
Verify size and ELF magic before normalizing only the asset's masked three bytes.
"""
import argparse
import hashlib
from pathlib import Path
import shutil

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('decoded', type=Path)
p.add_argument('apk', type=Path)
p.add_argument('output', type=Path)
a = p.parse_args()
expected = '628012f407d7df89b6d7064cc5be6e103d4a0652de7123ddddd4a2295b17759d'
if hashlib.file_digest(a.apk.open('rb'), 'sha256').hexdigest() != expected:
    raise ValueError('Expected audited 0.2.0 APK')
if a.output.exists():
    raise FileExistsError(a.output)
source = a.decoded/'smali/com/android/app/Application.smali'
if hashlib.sha256(source.read_bytes()).hexdigest() != 'a56024030ab7d1415882417c159c32ad70d7c0306dd246308c076e153f44157c':
    raise ValueError('Unexpected decoded Application class')
text = source.read_text(encoding='utf-8')
start = text.index('.method private static b()V')
end = text.index('.end method', start)
method = text[start:end]
site = '    invoke-static {v5}, Lcom/android/app/Application;->bc(Ljava/io/File;)J'
if method.count(site) != 1:
    raise ValueError('Unexpected ELF validation call')
method = method.replace(site,
    '    invoke-static {v5, v12}, Lcom/android/app/Application;->x6810ElfAssetCrc(Ljava/io/File;Ljava/util/zip/ZipEntry;)J')
text = text[:start]+method+text[end:]
text += '''
.method private static x6810ElfAssetCrc(Ljava/io/File;Ljava/util/zip/ZipEntry;)J
    .locals 9
    # Fail closed: CRC32 is unsigned, so -1 cannot match a valid ZIP CRC.
    invoke-virtual {p0}, Ljava/io/File;->length()J
    move-result-wide v6
    invoke-virtual {p1}, Ljava/util/zip/ZipEntry;->getSize()J
    move-result-wide v4
    cmp-long v8, v6, v4
    if-nez v8, :invalid_size
    const/4 v0, 0x0
    :try_start
    new-instance v8, Ljava/io/FileInputStream;
    invoke-direct {v8, p0}, Ljava/io/FileInputStream;-><init>(Ljava/io/File;)V
    move-object v0, v8
    invoke-virtual {v0}, Ljava/io/FileInputStream;->read()I
    move-result v3
    const/16 v4, 0x7f
    if-ne v3, v4, :bad_header
    invoke-virtual {v0}, Ljava/io/FileInputStream;->read()I
    move-result v3
    const/16 v4, 0x45
    if-ne v3, v4, :bad_header
    invoke-virtual {v0}, Ljava/io/FileInputStream;->read()I
    move-result v3
    const/16 v4, 0x4c
    if-ne v3, v4, :bad_header
    invoke-virtual {v0}, Ljava/io/FileInputStream;->read()I
    move-result v3
    const/16 v4, 0x46
    if-ne v3, v4, :bad_header
    new-instance v1, Ljava/util/zip/CRC32;
    invoke-direct {v1}, Ljava/util/zip/CRC32;-><init>()V
    const/4 v4, 0x0
    invoke-virtual {v1, v4}, Ljava/util/zip/CRC32;->update(I)V
    invoke-virtual {v1, v4}, Ljava/util/zip/CRC32;->update(I)V
    invoke-virtual {v1, v4}, Ljava/util/zip/CRC32;->update(I)V
    invoke-virtual {v1, v3}, Ljava/util/zip/CRC32;->update(I)V
    const/16 v5, 0x2000
    new-array v2, v5, [B
    :read_loop
    invoke-virtual {v0, v2}, Ljava/io/FileInputStream;->read([B)I
    move-result v3
    const/4 v5, -0x1
    if-eq v3, v5, :complete
    invoke-virtual {v1, v2, v4, v3}, Ljava/util/zip/CRC32;->update([BII)V
    goto :read_loop
    :complete
    invoke-virtual {v1}, Ljava/util/zip/CRC32;->getValue()J
    move-result-wide v6
    invoke-virtual {v0}, Ljava/io/FileInputStream;->close()V
    return-wide v6
    :bad_header
    invoke-virtual {v0}, Ljava/io/FileInputStream;->close()V
    :try_end
    .catch Ljava/io/IOException; {:try_start .. :try_end} :io_error
    goto :invalid_size
    :io_error
    move-exception v8
    if-eqz v0, :invalid_size
    :close_start
    invoke-virtual {v0}, Ljava/io/FileInputStream;->close()V
    :close_end
    .catch Ljava/io/IOException; {:close_start .. :close_end} :close_error
    goto :invalid_size
    :close_error
    move-exception v8
    :invalid_size
    const-wide/16 v6, -0x1
    return-wide v6
.end method
'''
shutil.copytree(a.decoded/'smali', a.output/'smali')
(a.output/'smali/com/android/app/Application.smali').write_text(text, encoding='utf-8')
print('Prepared isolated ELF CRC normalization:', a.output)
