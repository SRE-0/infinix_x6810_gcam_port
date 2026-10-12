"""Apply and restore small, verified BSG preview-lag preference experiments."""

import argparse
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "research" / "analysis" / "preview-lag-20260924"
PACKAGE = "com.android.MGC_9_7_047"
PREF = f"/data/user/0/{PACKAGE}/shared_prefs/{PACKAGE}_preferences.xml"
BASELINE = OUT / "mgc-prefs-baseline.xml"


def adb(*args: str) -> bytes:
    return subprocess.check_output(["adb", *args])


def replace_string(data: bytes, key: str, value: str) -> bytes:
    pattern = rb'(<string name="' + re.escape(key.encode()) + rb'">)[^<]*(</string>)'
    updated, count = re.subn(pattern, rb"\g<1>" + value.encode() + rb"\g<2>", data)
    if count != 1:
        raise RuntimeError(f"expected one {key!r}, found {count}")
    return updated


def set_string(data: bytes, key: str, value: str) -> bytes:
    if re.search(rb'<string name="' + re.escape(key.encode()) + rb'">', data):
        return replace_string(data, key, value)
    marker = b"</map>"
    if data.count(marker) != 1:
        raise RuntimeError("preferences XML has no unique </map> marker")
    entry = f'    <string name="{key}">{value}</string>\n'.encode()
    return data.replace(marker, entry + marker)


def replace_boolean(data: bytes, key: str, value: bool) -> bytes:
    pattern = rb'(<boolean name="' + re.escape(key.encode()) + rb'" value=")[^"]*(" />)'
    replacement = rb"\g<1>" + (b"true" if value else b"false") + rb"\g<2>"
    updated, count = re.subn(pattern, replacement, data)
    if count != 1:
        raise RuntimeError(f"expected one boolean {key!r}, found {count}")
    return updated


def set_boolean(data: bytes, key: str, value: bool) -> bytes:
    if re.search(rb'<boolean name="' + re.escape(key.encode()) + rb'" value="', data):
        return replace_boolean(data, key, value)
    marker = b"</map>"
    if data.count(marker) != 1:
        raise RuntimeError("preferences XML has no unique </map> marker")
    literal = "true" if value else "false"
    entry = f'    <boolean name="{key}" value="{literal}" />\n'.encode()
    return data.replace(marker, entry + marker)


def install(data: bytes, label: str) -> None:
    local = OUT / f"mgc-prefs-{label}.xml"
    local.write_bytes(data)
    adb("shell", "am", "force-stop", PACKAGE)
    adb("push", str(local), "/data/local/tmp/x6810-mgc-prefs.xml")
    adb("shell", "su", "-c", f"cp /data/local/tmp/x6810-mgc-prefs.xml {PREF}")
    live = adb("shell", "su", "-c", f"cat {PREF}").replace(b"\r", b"")
    if live != data.replace(b"\r", b""):
        raise RuntimeError("live preference verification failed")
    adb("shell", "monkey", "-p", PACKAGE, "-c", "android.intent.category.LAUNCHER", "1")
    print(f"{label}: installed, byte-verified, and BSG relaunched")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "action",
        choices=(
            "zsl3",
            "raw-yuv",
            "yuv-1600",
            "yuv-1280",
            "yuv-1280-dng",
            "yuv-optimized",
            "yuv-fast",
            "throttle-off",
            "hw-buffer",
            "hdr-off",
            "hdr-profile-shiba",
            "burst8",
            "restore",
        ),
    )
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    live = adb("shell", "su", "-c", f"cat {PREF}")
    if not BASELINE.exists():
        BASELINE.write_bytes(live)
    baseline = BASELINE.read_bytes()

    if args.action == "restore":
        install(baseline, "restored")
        return
    if args.action == "zsl3":
        install(replace_string(baseline, "gcam.zsl_buffer_size", "3"), "zsl3")
        return

    if args.action == "yuv-1600":
        data = baseline
        for camera_id in (0, 1, 2):
            data = replace_string(data, f"raw_key_{camera_id}", "35")
            data = set_string(data, f"raw_res_key_{camera_id}", "1600x1200")
        install(data, "yuv-1600")
        return
    if args.action == "yuv-1280":
        data = baseline
        for camera_id in (0, 1, 2):
            data = replace_string(data, f"raw_key_{camera_id}", "35")
            data = set_string(data, f"raw_res_key_{camera_id}", "1280x960")
        install(data, "yuv-1280")
        return
    if args.action == "yuv-1280-dng":
        data = baseline
        for camera_id in (0, 1, 2):
            data = replace_string(data, f"raw_key_{camera_id}", "35")
            data = set_string(data, f"raw_res_key_{camera_id}", "1280x960")
        data = replace_string(data, "pref_camera_raw_output_key", "1")
        install(data, "yuv-1280-dng")
        return
    if args.action == "yuv-optimized":
        data = baseline
        for camera_id, size in ((0, "1280x960"), (1, "960x720"), (2, "1280x960")):
            data = replace_string(data, f"raw_key_{camera_id}", "35")
            data = set_string(data, f"raw_res_key_{camera_id}", size)
        install(data, "yuv-optimized")
        return
    if args.action == "yuv-fast":
        data = baseline
        for camera_id in (0, 1, 2):
            data = replace_string(data, f"raw_key_{camera_id}", "35")
            data = set_string(data, f"raw_res_key_{camera_id}", "1280x960")
        data = set_boolean(data, "camera.auto_fps", False)
        data = set_boolean(data, "camera.auto_fps_default", False)
        data = set_boolean(data, "camera.force_low_light_fps", False)
        install(data, "yuv-fast")
        return

    if args.action == "throttle-off":
        data = baseline
        for camera_id in (0, 1, 2):
            data = set_string(data, f"preview_throttle_fps_key_{camera_id}", "0")
        install(data, "throttle-off")
        return

    if args.action == "hw-buffer":
        data = replace_boolean(baseline, "camera.enable_hw_buff_uflag", True)
        install(data, "hw-buffer")
        return
    if args.action == "hdr-off":
        data = replace_string(baseline, "pref_camera_hdr_plus_key", "off")
        install(data, "hdr-off")
        return
    if args.action == "hdr-profile-shiba":
        data = baseline
        for camera_id in (0, 1, 2):
            data = replace_string(data, f"device_hdrplus_key_{camera_id}", "shiba")
        install(data, "hdr-profile-shiba")
        return
    if args.action == "burst8":
        data = set_string(baseline, "gcam.max_burst_size", "8")
        data = set_string(data, "camera.cuttle.max_burst_size", "8")
        install(data, "burst8")
        return

    data = baseline
    for camera_id in (0, 1, 2):
        data = replace_string(data, f"raw_key_{camera_id}", "35")
    install(data, "raw-yuv")


if __name__ == "__main__":
    main()
