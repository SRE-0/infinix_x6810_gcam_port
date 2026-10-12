<div align="center">
<h1>Infinix X6810 GCam Port</h1>
<p>BSG V32 · Recommended profiles · Local research tools</p>
<p>By <a href="https://github.com/SRE-0">SRE-0</a></p>
</div>

<p align="center">
  <img src="https://raw.githubusercontent.com/SRE-0/SRE-0/90a97a564019ec898fbf6a22afc2c59fd2004cf2/githubBanner.png" alt="SRE-0 project banner" width="100%">
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Android-X6810--GL-9ece6a?style=for-the-badge&labelColor=1a1b26&logo=android&logoColor=white" alt="Android X6810-GL">
  <img src="https://img.shields.io/badge/Python-3.11+-7aa2f7?style=for-the-badge&labelColor=1a1b26&logo=python&logoColor=white" alt="Python 3.11+">
  <img src="https://img.shields.io/badge/Git-LFS-f7768e?style=for-the-badge&labelColor=1a1b26&logo=git&logoColor=white" alt="Git LFS">
  <img src="https://img.shields.io/badge/APatch-systemless-73daca?style=for-the-badge&labelColor=1a1b26" alt="APatch systemless">
</p>

<p align="center"><strong>English</strong> &middot; <a href="docs/es/README.md">Espa&#241;ol</a></p>

## GCam project

Tools, profiles and documentation for BSG Google Camera on the Infinix Zero X Neo **X6810-GL**. Camera RAW/OIS/HD48 and flash modules belong to the separate [RAW project](https://github.com/SRE-0/infinix_x6810_raw).

**BSG MGC_9.7.047_V32_MGC.apk** (`com.android.MGC_9_7_047`) was tested and works perfectly with [the recommended V32 profile](profiles/README.md) on Android 16 GSI. Telephoto OIS was tested and works correctly. You can install any compatible external GCam as a normal APK; the system module is optional.

## Current system module

`x6810_gcam_startup` **0.7.0** installs the original signed BSG V32 APK as a system app and supplies a separate, verified native cache-library replacement. It preserves the APK signature. Historical modified DEX/panel experiments are not part of this release.

The actual APK packaged by this module is retained in [the payload directory](gcam/apatch-startup/payload/) through Git LFS. The cache fix is supplied as `libgcastartup-cache.so`; it is not baked into or re-signed inside the APK.

```sh
git lfs install
git lfs pull
python scripts/validate.py
python scripts/build.py
```

Python 3.11+ is required. The builder uses the retained signed APK by default; `--apk` accepts the same checksum-verified original from another local path. ZIPs, recommended XML and checksums go to `dist/releases/`. Install the ZIP through APatch and reboot. The XML is imported manually, not applied automatically. [Installation and permissions](docs/INSTALLATION.md).

The system installer accepts API 30+, but only Android 16 GSI has device evidence. Android 11 compatibility and the reorganized packaging still need hardware validation.

## Recommended settings

[x6810-gcam-bsg-9.7-v32-recommended.xml](profiles/x6810-gcam-bsg-9.7-v32-recommended.xml) preserves the supplied settings byte for byte: 755 unique preferences with photo OIS enabled. DNG saving is disabled in this snapshot; enable it in the app if required. [Import instructions, key settings and hashes](profiles/README.md).

## Local research workflow

Decompilation takes place only in ignored `.local-private/` storage. The published tree and rewritten history contain no standalone smali, DEX or class dumps. Project-authored generators and patch/inspection tools remain available.

```sh
python scripts/decompile.py --plan
python scripts/decompile.py --apktool-jar /path/apktool.jar
```

[Local decompilation guide](docs/DECOMPILATION.md). Re-clone after the history rewrite; do not merge old branches back. Existing clones, forks and cached commit URLs may retain older objects.

- [Architecture and build inputs](docs/DEVELOPMENT.md)
- [Historical research reports](docs/RESEARCH.md)
- [Legal review](docs/LEGAL.md), [third-party notices](THIRD_PARTY_NOTICES.md) and [disclaimer](DISCLAIMER.md)

## Credits and disclaimer

Google Camera rights remain with Google and the respective licensors. Credit **BSG** for this port: [official distribution page](https://www.celsoazevedo.com/files/android/google-camera/dev-bsg/f/dl399/) and [BSG group](https://t.me/publicgroup_mgc_bsg). Their distribution page does not establish a blanket open-source or redistribution license for the entire APK.

Experimental software, supplied as-is without warranties to the fullest extent permitted by law. To that extent, SRE-0 and contributors disclaim liability for device damage, data loss, boot failures and other losses. Mandatory rights and non-excludable liability remain unaffected. This project is unaffiliated with Google, BSG, Infinix or MediaTek; see [the full disclaimer](DISCLAIMER.md).

## Contact

<p align="center">
  <a href="mailto:sergioandresp660@gmail.com"><img src="https://img.shields.io/badge/Email-f7768e?style=for-the-badge&labelColor=1a1b26&logo=gmail&logoColor=white" alt="Email"></a>
  <a href="https://sre-0.github.io/SRE-0_web"><img src="https://img.shields.io/badge/Website-bb9af7?style=for-the-badge&labelColor=1a1b26&logo=googlechrome&logoColor=white" alt="Website"></a>
</p>
