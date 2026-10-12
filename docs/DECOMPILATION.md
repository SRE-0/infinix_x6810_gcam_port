**English** | [Español](es/DECOMPILATION.md)

# Local decompilation

Install Java and Apktool separately; optionally install JADX. Upstream tools: [Apktool](https://apktool.org/), [JADX](https://github.com/skylot/jadx). Obtain permission to inspect or modify the APK under the rules applicable to you; this workflow does not grant third-party rights.

```sh
python scripts/decompile.py --plan
python scripts/decompile.py --apktool-jar /path/apktool.jar --plan
python scripts/decompile.py --apktool-jar /path/apktool.jar
```

The input defaults to the retained signed V32 APK. `--apk` accepts another local file for analysis. Output defaults to `.local-private/decompilation/<APK-SHA256>/`; `--output` must resolve beneath this repository's `.local-private/`. Existing outputs are rejected without deletion. `--jadx /path/to/jadx` optionally adds Java inspection. `--plan` prints the exact argument arrays without decoding or creating output.

A local provenance JSON records the input hash and commands. Run historical patch tools against the resulting local `apktool` tree, using their `--help` and dated reports. Project-authored instrumentation templates are generated under `.local-private/instrumentation-templates/`; no Google/BSG class dump is included in those templates. Benchmark tools are historical and not an automatic release step.

Never stage decoded trees, smali/DEX/class files, source dumps, caches, photos or device traces. Ignore rules and offline validation guard the public source tree. The retained APK is the explicit LFS binary exception, not a decoded source distribution.

The published GCam history was rewritten to remove standalone smali artifacts. Re-clone rather than merging old branches back. Old clones, forks and cached commit URLs can retain prior objects; a force-push does not erase every copy. [GitHub's history-removal limitations](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository).
