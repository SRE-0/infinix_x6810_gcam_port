# X6810 GCam system module and profile — v0.8.0

[English](README.md) · [Español](docs/es/README.md) · [RAW/OIS/flash project](https://github.com/SRE-0/infinix_x6810_raw)

This release contains the optional APatch system module for the Infinix Zero X Neo X6810-GL and the recommended BSG V32 settings profile.

Installer now derives from `template-module`: SRE-0 banner, module metadata, manager detection, numbered checks and closing footer. Existing payloads and admission checks are preserved.

## Downloads

- `x6810-gcam-system-0.8.0.zip` — system module with the original signed BSG 9.7 V32 APK and separate native cache-library fix.
- `x6810-gcam-bsg-9.7-v32-recommended.xml` — the supplied profile, renamed for this project and preserved byte for byte.
- `SHA256SUMS.txt` and `releases.json` — verify and identify the downloads.

The APK inside the module is the original signature-preserving `MGC_9.7.047_V32_MGC.apk`, package `com.android.MGC_9_7_047`, SHA-256:

`132e18273b3aafdb93e851f5db88156bd4f82c5032ad8de6594fa5a49ea6fe89`

The module extracts its 21 ARM64 libraries and supplies the cache fix separately as `libgcastartup.so` (SHA-256 `64cfcb3f598cdf3e75875bdd4cb8e8775a6763be15c3d2240d1d7ee0656f053a`). Historical modified DEX/panel experiments are not applied. The original signed APK is also retained in the repository through Git LFS.

## Recommended profile and compatibility

BSG `MGC_9.7.047_V32_MGC.apk`, package `com.android.MGC_9_7_047`, was tested and works perfectly with the supplied 755-setting profile on Android 16 GSI. Telephoto OIS was tested and works correctly. The XML SHA-256 is `1b4014581d5bc07b0b3678ba4cea6be7e3bef7cd7f532e51d02e8907aa0ee9f9`. Import the XML in BSG with **Load config**; the module does not apply it automatically. The saved profile leaves DNG saving disabled; enable it in the app if needed.

You can install any compatible external GCam as a regular APK; the system module is optional. The system installer admits API 30+, but only Android 16 GSI has device evidence. Android 11 behavior and the repackaged release ZIP were not tested on a phone.

Install the ZIP through APatch, reboot and review the [permissions and recovery guide](https://github.com/SRE-0/infinix_x6810_gcam_port/blob/main/docs/INSTALLATION.md). For RAW, OIS, JPEG HD48 or flash support, install one compatible variant from the [RAW project](https://github.com/SRE-0/infinix_x6810_raw).

## Verify or build

Compare all downloads with `SHA256SUMS.txt`. Python 3.11+ and Git LFS are required for a source build:

```sh
git lfs install
git lfs pull
python scripts/validate.py
python scripts/build.py
```

Read the [profile guide](https://github.com/SRE-0/infinix_x6810_gcam_port/blob/main/profiles/README.md), [build notes](https://github.com/SRE-0/infinix_x6810_gcam_port/blob/main/docs/DEVELOPMENT.md), [local decompilation guide](https://github.com/SRE-0/infinix_x6810_gcam_port/blob/main/docs/DECOMPILATION.md), and the [legal review](https://github.com/SRE-0/infinix_x6810_gcam_port/blob/main/docs/LEGAL.md).

## Legal, credits and risk notice

Credit BSG: [distribution page](https://www.celsoazevedo.com/files/android/google-camera/dev-bsg/f/dl399/) · [BSG public group](https://t.me/publicgroup_mgc_bsg). Google Camera and bundled third-party components retain their respective rights. Attribution and a checksum do not grant permission to redistribute the entire proprietary APK or its modifications. No blanket project license or whole-APK redistribution authorization is claimed.

Experimental software, provided as-is without warranties to the fullest extent permitted by law. System-app installation and root changes carry risks such as boot failure, data loss, permission exposure and device damage. Responsibility is excluded only to the lawful extent; mandatory rights and non-excludable liability remain. Read the [full disclaimer](https://github.com/SRE-0/infinix_x6810_gcam_port/blob/main/DISCLAIMER.md) and [third-party notices](https://github.com/SRE-0/infinix_x6810_gcam_port/blob/main/THIRD_PARTY_NOTICES.md).

---

# Español

Esta versión incluye el módulo opcional de sistema APatch para Infinix Zero X Neo X6810-GL y el perfil recomendado de BSG V32.

El instalador deriva de `template-module`: banner SRE-0, metadatos, detecci?n del gestor, pasos numerados y cierre. Se conservan los payloads y controles de compatibilidad.

## Descargas

- `x6810-gcam-system-0.8.0.zip`: módulo de sistema con el APK BSG 9.7 V32 original y firmado, y un arreglo de caché nativo separado.
- `x6810-gcam-bsg-9.7-v32-recommended.xml`: ajustes aportados, renombrados para el proyecto y conservados byte por byte.
- `SHA256SUMS.txt` y `releases.json`: verifican e identifican las descargas.

El APK dentro del módulo es `MGC_9.7.047_V32_MGC.apk`, paquete `com.android.MGC_9_7_047`, conservado con su firma original. SHA-256:

`132e18273b3aafdb93e851f5db88156bd4f82c5032ad8de6594fa5a49ea6fe89`

El módulo extrae 21 bibliotecas ARM64 y aporta por separado el arreglo como `libgcastartup.so` (SHA-256 `64cfcb3f598cdf3e75875bdd4cb8e8775a6763be15c3d2240d1d7ee0656f053a`). No aplica los antiguos parches DEX/panel. El APK firmado también se conserva en el repositorio mediante Git LFS.

## Perfil y compatibilidad

BSG `MGC_9.7.047_V32_MGC.apk`, paquete `com.android.MGC_9_7_047`, se probó y funciona perfectamente con el perfil de 755 ajustes en Android 16 GSI. El OIS del teleobjetivo se probó y funciona correctamente. SHA-256 del XML: `1b4014581d5bc07b0b3678ba4cea6be7e3bef7cd7f532e51d02e8907aa0ee9f9`. En BSG, importa el archivo con **Load config**; instalar el módulo no aplica el perfil. Guardar DNG está desactivado; actívalo en la app si lo necesitas.

Puedes instalar cualquier GCam externa compatible como APK normal; el módulo de sistema es opcional. El instalador admite API 30+, pero solo hay evidencia del teléfono en Android 16 GSI. Android 11 y el ZIP reorganizado no se probaron en el dispositivo.

Instala el ZIP desde APatch, reinicia y consulta la [guía de permisos y recuperación](https://github.com/SRE-0/infinix_x6810_gcam_port/blob/main/docs/es/INSTALLATION.md). Para RAW, OIS, JPEG HD48 o flash, instala una variante compatible del [proyecto RAW](https://github.com/SRE-0/infinix_x6810_raw).

## Verificar o construir

Compara las descargas con `SHA256SUMS.txt`. Para construir desde el código se requiere Python 3.11+ y Git LFS:

```sh
git lfs install
git lfs pull
python scripts/validate.py
python scripts/build.py
```

Consulta la [guía del perfil](https://github.com/SRE-0/infinix_x6810_gcam_port/blob/main/profiles/README.es.md), [construcción](https://github.com/SRE-0/infinix_x6810_gcam_port/blob/main/docs/es/DEVELOPMENT.md), [decompilación local](https://github.com/SRE-0/infinix_x6810_gcam_port/blob/main/docs/es/DECOMPILATION.md) y [revisión legal](https://github.com/SRE-0/infinix_x6810_gcam_port/blob/main/docs/es/LEGAL.md).

## Aviso legal y créditos

Crédito a BSG: [página de distribución](https://www.celsoazevedo.com/files/android/google-camera/dev-bsg/f/dl399/) · [grupo público](https://t.me/publicgroup_mgc_bsg). Google Camera y los componentes incluidos conservan sus derechos. La atribución y el hash no conceden permiso para redistribuir todo el APK propietario o sus modificaciones. No se declara una licencia global ni permiso general para todo el APK.

Software experimental, proporcionado tal cual y sin garantías en la máxima medida permitida por la ley. Instalar una app de sistema y cambiar root implica riesgos de fallo de arranque, pérdida de datos, exposición de permisos y daños al dispositivo. La responsabilidad se excluye solo en la medida legal; siguen vigentes los derechos obligatorios y responsabilidades no excluibles. Lee el [descargo completo](https://github.com/SRE-0/infinix_x6810_gcam_port/blob/main/docs/es/DISCLAIMER.md) y los [avisos de terceros](https://github.com/SRE-0/infinix_x6810_gcam_port/blob/main/docs/es/THIRD_PARTY_NOTICES.md).
