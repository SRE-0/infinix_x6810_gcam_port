**English** | [Español](es/DEVELOPMENT.md)

# Architecture and builds

Python 3.11+ and Git LFS are required. The release builder uses the standard library and never downloads an APK implicitly.

```sh
git lfs install
git lfs pull
python scripts/validate.py
python scripts/build.py
```

The resulting ZIP, recommended XML and SHA-256 manifest go to `dist/releases/`. `--apk` can override the retained input, but the original signed V32 checksum remains mandatory. `--output` selects another build directory; the underlying builder refuses to overwrite an existing ZIP.

| Path | Responsibility |
|---|---|
| `scripts/` | Public build, offline validation and local decompilation entry points |
| `gcam/apatch-startup/` | Current system installer, permissions and pinned APK/native payloads |
| `gcam/apk-analysis/` | Historical inspection/patch tools and project-authored helper generators |
| `gcam/startup/` | Historical startup experiments |
| `tools/` | Historical configuration and analysis commands |
| `profiles/` | Recommended V32 snapshot; historical V18 overlay |
| `.local-private/` | Ignored decompilation, instrumentation and private data |
| `dist/` | Ignored generated release packages |

The builder retains the original APK intact and extracts its 21 ARM64 libraries, replacing only the separately mounted `libgcastartup.so`. The native SHA-256 is `64cfcb3f598cdf3e75875bdd4cb8e8775a6763be15c3d2240d1d7ee0656f053a`. APK integrity, XML permissions, native inventory and final ZIP are checked. The profile validator checks all 755 unique keys and enabled photo OIS.

Do not commit decoded APK resources, DEX, smali or JADX output. Standalone smali helper files were removed from repository history; Python tools generate the project's own instrumentation helpers locally. Follow [local decompilation](DECOMPILATION.md). Historical tools can require Apktool, Frida, ADB, target firmware and missing local data; some alter device state and are not run by release builds. [Legal review](LEGAL.md).

Installer presentation is derived at build time from `template-module/customize.sh` by `scripts/module_template.py`. Module-specific checks and boot scripts remain owned by their project.
