[English](../DEVELOPMENT.md) | **Español**

# Arquitectura

`scripts/build.py` es el único comando público de empaquetado; delega en el
constructor verificado de `gcam/apatch-startup/build.py`. `scripts/validate.py`
revisa sintaxis, XML, metadata y hash nativo sin conectar un dispositivo.
`gcam/apatch-startup/` contiene instalación, permisos y montaje del release.
`profiles/` contiene el snapshot V32 recomendado y conserva el overlay V18 como historia.

`gcam/apk-analysis/` y `gcam/startup/` son laboratorios históricos. Sus comandos
pueden necesitar apktool, Frida, ADB y datos locales ausentes, y algunos modifican
el estado del teléfono. No participan en la construcción del release.
Las herramientas históricas `*_mgc_*.py` están en `tools/`, a la misma profundidad
para conservar sus rutas relativas. `scripts/` contiene sólo build y validate.

El APK se proporciona con `--apk`; el proyecto no lo descarga implícitamente.
La biblioteca nativa está fijada por SHA-256
`64cfcb3f598cdf3e75875bdd4cb8e8775a6763be15c3d2240d1d7ee0656f053a`.
El builder extrae las 21 bibliotecas ARM64 del APK, reemplaza sólo
`libgcastartup.so` y conserva el APK original completo.

Los índices SQLite, descompilaciones, vídeos y benchmarks generados van a
`dist/` o `.local-private/`. El árbol RAW está en
[su propio repositorio](https://github.com/SRE-0/infinix_x6810_raw).

El builder entrega `x6810-gcam-bsg-9.7-v32-recommended.xml` por separado con
SHA-256; el validador comprueba integridad, 755 claves únicas y OIS fotográfico
habilitado. No lo aplica a la app ni lo mezcla con el overlay V18 histórico.
