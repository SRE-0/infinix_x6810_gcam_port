# GCam: release y laboratorios

Guía vigente: [instalación](../docs/INSTALLATION.md) e
[índice de investigación](../docs/RESEARCH.md). RAW/OIS/flash está en
[infinix_x6810_raw](https://github.com/SRE-0/infinix_x6810_raw).

`apatch-startup/` contains the separate APatch module that installs the
hash-verified BSG 9.7 V32 original signed APK as a privileged system app, grants its declared runtime
permissions and special accesses, and retains the native cache fix. The
`apk-analysis/` and `startup/` directories preserve tooling and investigations.

GCam photo settings are documented separately for BSG 9.7 V18 under
`profiles/`; that XML does not install with or configure the V32 system-app
module. See the [current GCam guide](../docs/INSTALLATION.md).
