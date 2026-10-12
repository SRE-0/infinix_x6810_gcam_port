# GCam profiles

- `gcam-bsg-v18.json` records sensor-specific experimental and neutral
  preferences used by the analysis/apply script. It does not claim a
  repeatable image-quality improvement.
- `x6810-gcam-bsg-v18-recommended.xml` is the small neutral overlay selected
  for release. It targets BSG 9.7 V18 and includes only the project's
  sensor-specific noise factors plus conservative focus/AWB/HDR+ controls.

The XML is not a complete app backup. Use it with
`scripts/configure_mgc_photo.py --profile-xml ...`, which merges the values,
backs up the existing preferences, checks the target APK, and verifies the
write. See the [localized GCam guide](../docs/es/GCAM.md) or
[English guide](../docs/en/GCAM.md).
