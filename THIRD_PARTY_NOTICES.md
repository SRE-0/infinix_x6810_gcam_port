**English** | [Español](docs/es/THIRD_PARTY_NOTICES.md)

# Third-party notices — GCam

## Google Camera and the BSG port

Google Camera is third-party software; Google and other licensors retain their rights. This project uses BSG's [MGC_9.7.047_V32 distribution](https://www.celsoazevedo.com/files/android/google-camera/dev-bsg/f/dl399/), package `com.android.MGC_9_7_047`. Credit **BSG**, the [distribution page](https://www.celsoazevedo.com/files/android/google-camera/dev-bsg/f/dl399/) and [BSG's public group](https://t.me/publicgroup_mgc_bsg), as requested by that page.

The retained payload APK and the APK inside the system module are the original signed V32, SHA-256 `132e18273b3aafdb93e851f5db88156bd4f82c5032ad8de6594fa5a49ea6fe89`. The separate native cache replacement is SHA-256 `64cfcb3f598cdf3e75875bdd4cb8e8775a6763be15c3d2240d1d7ee0656f053a`. These hashes and attribution are not a blanket redistribution license. This review did not establish an explicit license grant for republishing or modifying the entire Google/BSG APK or native library.

## Notices embedded in the retained APK

The original APK, including its embedded notices, is preserved intact. Three notice resources are additionally retained under [legal/gcam-apk](legal/gcam-apk/): `third_party_licenses`, `third_party_licenses_metadata` and `third_party_license_metadata`, exported as `.txt`. [Resource manifest](legal/gcam-apk/manifest.json) records the APK hash, original paths, sizes and resource hashes. They are license notices, not a decoded app source tree.

Those resources describe incorporated third-party components. Their licenses apply to the covered components; they do not establish that the whole proprietary APK is open source. The exported texts are unchanged. Applicable Apache, BSD or other terms must be followed for their respective components; an exhaustive component/source mapping was not established.

## Native modification and local tools

The system module substitutes a separate mounted native library; it does not modify or re-sign the APK. Historical patch tools do not contain a distributable decoded Google/BSG class tree. Project-authored `x6810.gcam` helper templates generate instrumentation only in ignored local storage. Local analysis does not itself grant permission for later distribution; reverse-engineering exceptions depend on applicable law and agreements.

## Repository-owned material

No blanket license has been selected for original project scripts, documentation, patches or profiles. Public availability alone does not establish a general permission to modify or redistribute them. GitHub distinguishes public repository access from licensing: [licensing a repository](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/licensing-a-repository). Separate component licenses remain effective. The disclaimer does not override them.

## External tools

Python/Git/Git LFS, ADB, Apktool, JADX, Frida and analysis dependencies are external development tools; invoking them does not transfer their licenses to every output or to this entire repository. Keep their upstream notices if redistributing them. The release builders use Python's standard library; historical tools have their own requirements and are not bundled as installed dependencies. No comprehensive software bill of materials for third-party firmware/APK internals is claimed.

## Trademarks

Google, Android, Infinix, MediaTek, Transsion and BSG names identify products, compatibility or authors. No endorsement, trademark license or affiliation is claimed.

RAW/vendor/AOSP notices are maintained in [the RAW repository](https://github.com/SRE-0/infinix_x6810_raw). See [legal review](docs/LEGAL.md) and [disclaimer](DISCLAIMER.md).
