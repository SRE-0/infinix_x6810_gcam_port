"""Collect a process-cold BSG launch via ADB; keep private output under dist/.

Does not clear app data, system caches or log buffers. Force-stops only GCam.
am start measures initial display, NOT a working camera preview. Screenshots
and HAL/app timestamps must be inspected separately. Unlock the phone first.
"""
import argparse
from datetime import date
import json
from pathlib import Path
import re
import subprocess
import time

PACKAGE = "com.android.MGC_9_7_047"
COMPONENT = PACKAGE + "/com.android.camera.CameraLauncher"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--serial", required=True)
    parser.add_argument("--label", required=True)
    parser.add_argument("--output", type=Path,
                        default=Path("dist/analysis") / ("startup-" + date.today().strftime("%Y%m%d")))
    parser.add_argument("--seconds", type=int, default=15)
    parser.add_argument("--screenshots", default="3,6,10")
    args = parser.parse_args()
    if not re.fullmatch(r"[a-zA-Z0-9_-]+", args.label):
        parser.error("Use a simple label without path separators")
    shots = sorted(set(int(s) for s in args.screenshots.split(",") if s))
    if not 3 <= args.seconds <= 60 or any(s < 0 or s > args.seconds for s in shots):
        parser.error("Duration must be 3..60 seconds; screenshots must fall within it")
    out = args.output / args.label
    adb = ["adb", "-s", args.serial]

    def run(*parts):
        return subprocess.check_output(adb + list(parts), timeout=35)

    if run("get-state").strip() != b"device":
        raise RuntimeError("Device not authorized/connected")
    out.mkdir(parents=True, exist_ok=False)
    run("shell", "am", "force-stop", PACKAGE)
    time.sleep(2)
    run("shell", "cmd", "statusbar", "collapse")
    (out / "memory-before.txt").write_bytes(run("shell", "cat", "/proc/meminfo"))
    events = []
    launch = None
    with (out / "logcat.txt").open("wb") as log, (out / "logcat-stderr.txt").open("wb") as err:
        logger = subprocess.Popen(adb + ["logcat", "-b", "main", "-b", "system", "-b", "events",
                                         "-v", "threadtime", "-T", "1"], stdout=log, stderr=err)
        try:
            run("shell", "log", "-t", "X6810_STARTUP", args.label)
            start = time.monotonic()
            launch = subprocess.Popen(adb + ["shell", "am", "start", "-W", "-n", COMPONENT],
                                      stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            for second in shots:
                time.sleep(max(0, start + second - time.monotonic()))
                begin = time.monotonic() - start
                data = run("exec-out", "screencap", "-p")
                end = time.monotonic() - start
                (out / f"screen-{second}s.png").write_bytes(data)
                events.append(dict(requested_seconds=second, begin=begin, end=end))
            time.sleep(max(0, start + args.seconds - time.monotonic()))
            stdout, stderr = launch.communicate(timeout=20)
            (out / "am-start.txt").write_bytes(stdout)
            (out / "am-start-stderr.txt").write_bytes(stderr)
            if launch.returncode or b"Status: ok" not in stdout:
                raise RuntimeError("Launch failed; inspect am-start output")
            pid = run("shell", "pidof", PACKAGE).decode().strip()
        finally:
            if launch is not None and launch.poll() is None:
                launch.terminate()
                launch.wait(timeout=5)
            (out / "logcat-health.json").write_text(json.dumps({
                "exit_code_before_stop": logger.poll(),
                "elapsed_seconds": time.monotonic() - start if 'start' in locals() else None,
            }, indent=2) + "\n")
            logger.terminate()
            logger.wait(timeout=5)
    lines = (out / "logcat.txt").read_text(errors="replace").splitlines()
    app = [line for line in lines if re.search(r"\s" + re.escape(pid) + r"\s+\d+\s", line)]
    (out / "app-logcat.txt").write_text("\n".join(app) + "\n", encoding="utf-8")
    key = re.compile(r"X6810_STARTUP|Displayed .*MGC|configureStreams_3_6|CameraService::connect call|"
                     r"Choreographer: Skipped|ModeSwitcher WAS ALREADY|Null OIS keys|OIS is dead|"
                     r"Prewarm of microvideo|setupVideoEncoder succeeded|FATAL EXCEPTION|ANR in")
    selected = [line for line in lines if key.search(line)]
    (out / "timeline.txt").write_text("\n".join(selected) + "\n", encoding="utf-8")
    total = re.search(rb"TotalTime:\s*(\d+)", stdout)
    summary = dict(label=args.label, pid=pid, initial_display_ms=int(total[1]) if total else None,
                   screenshots=events, preview_ready_ms=None,
                   note="Preview readiness requires visual review; initial display is not readiness.")
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary))


if __name__ == "__main__":
    main()
