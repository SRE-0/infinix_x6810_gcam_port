"""Build the hash-verified GCam system-app and startup APatch module."""
import argparse
import hashlib
from pathlib import Path
import xml.etree.ElementTree as ET
import zipfile

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('apk', type=Path)
p.add_argument('output', type=Path)
p.add_argument('--native', type=Path, required=True, help='Hash-verified cache-path native library')
a = p.parse_args()
expected = '132e18273b3aafdb93e851f5db88156bd4f82c5032ad8de6594fa5a49ea6fe89'
if hashlib.file_digest(a.apk.open('rb'), 'sha256').hexdigest()!=expected:
    raise ValueError('The system app must use the original, signature-preserving APK payload')
native_expected = '64cfcb3f598cdf3e75875bdd4cb8e8775a6763be15c3d2240d1d7ee0656f053a'
if hashlib.file_digest(a.native.open('rb'), 'sha256').hexdigest() != native_expected:
    raise ValueError('Unexpected native payload')
if a.output.exists():
    raise FileExistsError(a.output)
a.output.parent.mkdir(parents=True, exist_ok=True)
with zipfile.ZipFile(a.apk) as apk_archive:
    native_members = sorted(
        name for name in apk_archive.namelist()
        if name.startswith('lib/arm64-v8a/') and name.endswith('.so')
    )
    if len(native_members) != 21 or not any(name.endswith('/libgcastartup.so') for name in native_members):
        raise ValueError('Unexpected ARM64 native library inventory in the verified APK')

permission_xml = Path(__file__).with_name('system') / 'etc/default-permissions/permissions_x6810_gcam.xml'
if not permission_xml.is_file():
    raise FileNotFoundError(permission_xml)
permission_root = ET.parse(permission_xml).getroot()
expected_permissions = {
    'android.permission.CAMERA',
    'android.permission.RECORD_AUDIO',
    'android.permission.ACCESS_COARSE_LOCATION',
    'android.permission.ACCESS_FINE_LOCATION',
    'android.permission.NEARBY_WIFI_DEVICES',
    'android.permission.READ_EXTERNAL_STORAGE',
    'android.permission.WRITE_EXTERNAL_STORAGE',
    'android.permission.READ_MEDIA_IMAGES',
    'android.permission.READ_MEDIA_VIDEO',
    'android.permission.READ_MEDIA_VISUAL_USER_SELECTED',
    'android.permission.POST_NOTIFICATIONS',
}
if (permission_root.tag != 'exceptions' or len(permission_root) != 1 or
        permission_root[0].attrib != {'package': 'com.android.MGC_9_7_047'} or
        {permission.get('name') for permission in permission_root[0]} != expected_permissions or
        any(permission.get('fixed') != 'false' for permission in permission_root[0])):
    raise ValueError('Unexpected GCam default runtime-permission allowlist')
privileged_root = ET.parse(Path(__file__).parent / 'system/etc/permissions/privapp-permissions-x6810-gcam.xml').getroot()
if (privileged_root.tag != 'permissions' or len(privileged_root) != 1 or
        privileged_root[0].tag != 'privapp-permissions' or
        privileged_root[0].attrib != {'package': 'com.android.MGC_9_7_047'} or
        len(privileged_root[0]) != 1 or
        privileged_root[0][0].attrib != {'name': 'android.permission.INSTALL_PACKAGE_UPDATES'}):
    raise ValueError('Unexpected privileged permission allowlist')
with zipfile.ZipFile(a.output, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=3) as archive:
    for name in (
        'module.prop', 'customize.sh', 'service.sh', 'uninstall.sh', 'activate.sh',
        'system/etc/default-permissions/permissions_x6810_gcam.xml',
        'system/etc/permissions/privapp-permissions-x6810-gcam.xml',
        'permissions.sh',
    ):
        data = Path(__file__).parent.joinpath(*name.split('/')).read_bytes().replace(b'\r\n', b'\n')
        info = zipfile.ZipInfo(name)
        info.create_system = 3
        info.external_attr = (0o100755 if name.endswith('.sh') else 0o100644)<<16
        archive.writestr(info, data)
    archive.write(a.apk, 'system/priv-app/X6810GCam/X6810GCam.apk', compress_type=zipfile.ZIP_STORED)
    with zipfile.ZipFile(a.apk) as apk_archive:
        for member in native_members:
            filename = member.rsplit('/', 1)[-1]
            data = a.native.read_bytes() if filename == 'libgcastartup.so' else apk_archive.read(member)
            info = zipfile.ZipInfo(f'system/priv-app/X6810GCam/lib/arm64/{filename}')
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            archive.writestr(info, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=3)
with zipfile.ZipFile(a.output) as archive:
    if archive.testzip() is not None:
        raise ValueError('Invalid module archive')
    names = set(archive.namelist())
    native_paths = {
        name for name in names
        if name.startswith('system/priv-app/X6810GCam/lib/arm64/') and name.endswith('.so')
    }
    expected_native_paths = {
        f"system/priv-app/X6810GCam/lib/arm64/{name.rsplit('/', 1)[-1]}"
        for name in native_members
    }
    if ('skip_mount' in names or 'system/priv-app/X6810GCam/X6810GCam.apk' not in names or
            native_paths != expected_native_paths):
        raise ValueError('Module must expose the GCam system overlay before boot scanning')
    with zipfile.ZipFile(a.apk) as apk_archive:
        for member in native_members:
            filename = member.rsplit('/', 1)[-1]
            packaged = archive.read(f'system/priv-app/X6810GCam/lib/arm64/{filename}')
            expected_hash = native_expected if filename == 'libgcastartup.so' else hashlib.sha256(apk_archive.read(member)).hexdigest()
            if hashlib.sha256(packaged).hexdigest() != expected_hash:
                raise ValueError(f'Unexpected packaged native library: {filename}')
print(f'Created GCam system-app APatch module with {len(native_members)} ARM64 libraries:', a.output)
