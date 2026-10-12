**English** | [Español](es/LEGAL.md)

# Legal review — GCam

| Material | Evidence | Remaining issue |
|---|---|---|
| Original signed BSG V32 APK | Verified original bytes, BSG distribution page and attribution request | Explicit whole-APK redistribution/modification grant not established |
| Native cache fix | Verified library and historical patch research | Underlying proprietary library rights remain applicable |
| Embedded license resources | Three exact resources retained with hashes | Notices do not establish a complete component/source compliance inventory |
| Inspection/patch tools and helper generators | Project-authored tools; decoded inputs local-only | Local legality and agreements vary; no blanket project license selected |
| Recommended XML | Supplied configuration snapshot, unchanged | Not a grant of rights in Google/BSG software |

## What this review establishes

This is a component and source review dated **2026-10-12**, not a legal opinion for a particular country. The applicable country, distribution arrangement and exact proprietary agreements have not been established. A public link, successful test, device ownership or “research” label is not automatically a copyright or redistribution permission.

The review distinguishes provenance (where bytes came from), licensing (which rights were granted), engineering compatibility and liability. None substitutes for the others. Hashes establish integrity only. Removing decompiled material improves repository boundaries but does not resolve the rights attached to a retained proprietary binary.

## Warranty and liability

[DISCLAIMER.md](../DISCLAIMER.md) provides a project-specific as-is statement and an exclusion of responsibility to the lawful extent, including device damage, lost data and boot failures. It preserves mandatory rights and non-excludable liability. Similar limitations in upstream licenses are component terms, not proof that one project notice guarantees worldwide enforceability. No universal waiver or choice of jurisdiction is claimed.

[Google's general terms](https://policies.google.com/terms) and [Infinix's published service terms](https://activity.infinixmobility.com/termsuse) illustrate that rights and liability depend on the applicable agreement and law; they are not substituted for an unavailable APK-specific or X6810 firmware agreement. A regional hardware warranty cannot be generalized to all users.

## Before redistributing material

Determine the exact rights holder and agreement for each shipped binary, including modifications; obtain permissions where needed. Keep component license texts and copyright notices. For covered open-source components, satisfy their own notice/source obligations. Assess local reverse-engineering, copyright, trademark, warranty and consumer rules with qualified advice. Do not present this repository's disclaimer as a license grant or legal immunity.

If a rights holder objects, identify the exact path/version, rights basis and requested remedy through the project contact in the README. Attribution alone does not settle permission. This documentation records unresolved provenance and licensing honestly rather than declaring the entire project cleared.

## GCam-specific findings

BSG's V32 page requests credit to BSG and links to its distribution and public group. Those requests are honored in the README and notices. No full-APK open-source license or blanket authorization to republish modified binaries was found on that distribution page. [BSG V32 source page](https://www.celsoazevedo.com/files/android/google-camera/dev-bsg/f/dl399/).

Google's general terms do not by themselves establish the complete license for this third-party port. Android/AOSP open-source licensing does not automatically cover Google Camera. Open-source notice resources inside the APK remain component-specific. The APK is retained as requested, but this review does not represent that all distribution rights have been cleared.

The published source tree excludes decoded resources and standalone bytecode dumps. Analysis is performed in ignored local storage with separately installed tools. That boundary does not guarantee that reverse engineering is lawful everywhere or override a binding agreement. Any published patch/output must be assessed separately.

The optional system module grants runtime permissions and special accesses; users should understand the storage/settings/Do Not Disturb implications and retained permissions after removal. The original signature is preserved, not converted to a platform signature. [Installation](INSTALLATION.md), [third-party notices](../THIRD_PARTY_NOTICES.md), [local decompilation](DECOMPILATION.md).
