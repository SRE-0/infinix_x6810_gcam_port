# Infinix X6810-GL — GCam port

Proyecto independiente de análisis y modificación de BSG Google Camera para
X6810-GL. El módulo de RAW, OIS y flash está en
[infinix_x6810_raw](https://github.com/SRE-0/infinix_x6810_raw).

El release actual `x6810_gcam_startup` 0.7.0 instala el APK BSG 9.7 V32 **original
firmado** como app privilegiada y sustituye la biblioteca nativa de caché.
Los ensayos históricos modificados del DEX/panel no son el APK del release actual.
Este repo conserva sus fuentes de investigación; el APK modificado 0.5.0 se
conserva localmente fuera de Git. No instala el módulo RAW.

```sh
git lfs install
git lfs pull
python scripts/validate.py
python scripts/build.py --apk /ruta/MGC_9.7.047_V32_MGC.apk
```

Necesita Python 3.11+ y el APK original con SHA-256
`132e18273b3aafdb93e851f5db88156bd4f82c5032ad8de6594fa5a49ea6fe89`.
La biblioteca caché permanece en Git LFS. Los ZIP y checksums se generan en
`dist/releases/`; los APK y paquetes generados están excluidos del repositorio.

- [Instalación y límites](docs/INSTALLATION.md)
- [Arquitectura y construcción](docs/DEVELOPMENT.md)
- [Investigaciones y versiones históricas](docs/RESEARCH.md)
- [Avisos de terceros](THIRD_PARTY_NOTICES.md)

La evidencia previa corresponde a Android 16 GSI. El instalador admite SDK 30+,
pero eso no demuestra que el APK, permisos y montaje funcionen en Android 11.
Puedes instalar cualquier GCam externa compatible como APK normal, sin este
módulo de sistema. Su builder fija V32 únicamente para el release de sistema.
El propietario confirma que
[MGC_9.7.047_V32_MGC.apk](https://1-dontsharethislink.celsoazevedo.com/file/filesc/MGC_9.7.047_V32_MGC.apk)
(`com.android.MGC_9_7_047`) funciona perfectamente con
[x6810-gcam-bsg-9.7-v32-recommended.xml](profiles/x6810-gcam-bsg-9.7-v32-recommended.xml)
en Android 16 GSI. OIS del teleobjetivo también se probó y funciona correctamente.
[Guía del perfil recomendado](profiles/README.md).

El XML V32 es el perfil recomendado actual, conserva las 755 preferencias
aportadas por el propietario y se incluye como archivo separado en los releases.
El pequeño overlay V18 se conserva sólo como referencia histórica.
