**English** | [Español](README.es.md)

# APK analysis tools

Historical inspection, instrumentation and patch tools for the X6810 BSG experiments. The current 0.7.0 system module preserves the signed original APK and supplies a separate native cache fix; older DEX/panel trials are not part of that release.

[Local decompilation](../../docs/DECOMPILATION.md) supplies the input trees. Standalone smali files are excluded from Git; `helper_templates.py` generates the project-authored `x6810.gcam` helpers in `.local-private/instrumentation-templates/`. Use each tool's `--help`; inputs and device assumptions are specific to the dated investigation.

[Original analysis and measurements in Spanish](README.es.md), [research index](../../docs/RESEARCH.md), [current module](../apatch-startup/README.md). Reports describe their dated state, not the present release.
