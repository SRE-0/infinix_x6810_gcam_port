<div align="center">
<h1>Infinix X6810 GCam Port</h1>
<p>BSG V32 · Perfiles recomendados · Herramientas de investigación local</p>
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

<p align="center"><a href="../../README.md">English</a> &middot; <strong>Espa&#241;ol</strong></p>

## Proyecto GCam

Herramientas, perfiles y documentación de BSG Google Camera para **X6810-GL**. Los módulos RAW/OIS/HD48 y flash se encuentran en [el proyecto RAW](https://github.com/SRE-0/infinix_x6810_raw).

**BSG MGC_9.7.047_V32_MGC.apk**, paquete `com.android.MGC_9_7_047`, se probó y funciona perfectamente con [el perfil V32 recomendado](../../profiles/README.es.md) en Android 16 GSI. OIS del teleobjetivo se probó y funciona correctamente. Puedes instalar cualquier GCam externa compatible como APK normal; el módulo de sistema es opcional.

## Módulo de sistema actual

`x6810_gcam_startup` **0.7.0** instala el APK original firmado de BSG V32 y una biblioteca nativa de caché independiente. No modifica la firma del APK ni aplica los ensayos históricos de DEX/panel. El APK que realmente usa el módulo y la biblioteca se conservan mediante Git LFS en `gcam/apatch-startup/payload/`.

```sh
git lfs install
git lfs pull
python scripts/validate.py
python scripts/build.py
```

Python 3.11+. `--apk` permite proporcionar el mismo original verificado desde otra ruta local. ZIP, XML y hashes van a `dist/releases/`. Instala desde APatch y reinicia; importa el XML manualmente. [Instalación](INSTALLATION.md). El instalador admite API 30+, pero solo existen pruebas en Android 16 GSI; Android 11 y el empaquetado reorganizado siguen sin validarse en hardware.

## Ajustes e investigación local

El [XML recomendado](../../profiles/x6810-gcam-bsg-9.7-v32-recommended.xml) conserva 755 preferencias sin alterar, con OIS fotográfico activado. Guardar DNG está desactivado en el snapshot; actívalo en la app si lo necesitas. [Guía del perfil](../../profiles/README.es.md).

La decompilación solo genera archivos en `.local-private/`, ignorado por Git. Se conservaron herramientas y generadores propios; se retiraron los smali independientes del árbol y del historial publicado.

```sh
python scripts/decompile.py --plan
python scripts/decompile.py --apktool-jar /ruta/apktool.jar
```

[Decompilación local](DECOMPILATION.md). Vuelve a clonar tras la reescritura del historial; clones, forks y URLs antiguas en caché pueden conservar objetos previos.

- [Arquitectura y construcción](DEVELOPMENT.md)
- [Informes históricos](RESEARCH.md)
- [Revisión legal](LEGAL.md), [avisos de terceros](THIRD_PARTY_NOTICES.md) y [descargo](DISCLAIMER.md)

## Créditos y descargo

Google y sus licenciantes conservan los derechos sobre Google Camera. El port es de **BSG**: [distribución](https://www.celsoazevedo.com/files/android/google-camera/dev-bsg/f/dl399/) y [grupo](https://t.me/publicgroup_mgc_bsg). Su página no establece una licencia abierta ni permiso general para todo el APK.

Software experimental proporcionado tal cual, sin garantías, en la máxima medida permitida por la ley. En esa medida, SRE-0 y colaboradores excluyen responsabilidad por daños, pérdidas y fallos derivados de su uso. Se mantienen los derechos y responsabilidades no excluibles. Proyecto independiente sin afiliación con Google, BSG, Infinix ni MediaTek. [Descargo completo](DISCLAIMER.md).

## Contacto

<p align="center">
  <a href="mailto:sergioandresp660@gmail.com"><img src="https://img.shields.io/badge/Email-f7768e?style=for-the-badge&labelColor=1a1b26&logo=gmail&logoColor=white" alt="Email"></a>
  <a href="https://sre-0.github.io/SRE-0_web"><img src="https://img.shields.io/badge/Website-bb9af7?style=for-the-badge&labelColor=1a1b26&logo=googlechrome&logoColor=white" alt="Website"></a>
</p>
