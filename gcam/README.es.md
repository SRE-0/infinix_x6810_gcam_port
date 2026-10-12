[English](README.md) | **Español**

# GCam: release y laboratorios

Guía vigente: [instalación](../docs/INSTALLATION.md) e
[índice de investigación](../docs/RESEARCH.md). RAW/OIS/flash está en
[infinix_x6810_raw](https://github.com/SRE-0/infinix_x6810_raw).

`apatch-startup/` contains the separate APatch module that installs the
hash-verified BSG 9.7 V32 original signed APK as a privileged system app, grants its declared runtime
permissions and special accesses, and retains the native cache fix. The
`apk-analysis/` and `startup/` directories preserve tooling and investigations.

The recommended profile is now the owner-provided BSG 9.7 V32 snapshot in
`profiles/x6810-gcam-bsg-9.7-v32-recommended.xml`; the V18 overlay is historical.
The XML is imported manually and does not apply automatically at system-module
boot. Any compatible external GCam can be installed independently. See the
[profile guide](../profiles/README.md) and [installation](../docs/INSTALLATION.md).
