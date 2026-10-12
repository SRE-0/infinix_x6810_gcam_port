[English](../DECOMPILATION.md) | **Español**

# Decompilación local

Instala Java y [Apktool](https://apktool.org/) por separado; [JADX](https://github.com/skylot/jadx) es opcional. Comprueba que puedes analizar o modificar el APK conforme a las condiciones y leyes aplicables.

```sh
python scripts/decompile.py --plan
python scripts/decompile.py --apktool-jar /ruta/apktool.jar --plan
python scripts/decompile.py --apktool-jar /ruta/apktool.jar
```

La entrada predeterminada es el APK firmado V32 conservado. `--apk` permite analizar otro archivo local. La salida es `.local-private/decompilation/<SHA256-del-APK>/`; `--output` solo admite un subdirectorio de `.local-private/` de este repositorio. Se rechazan salidas existentes sin borrarlas. `--jadx /ruta/jadx` añade inspección Java. `--plan` muestra comandos sin decompilar ni crear salidas.

Un JSON local registra hash y comandos. Ejecuta las herramientas históricas sobre el árbol local `apktool`, siguiendo su ayuda e informes fechados. Las plantillas propias de instrumentación se generan en `.local-private/instrumentation-templates/`; no contienen clases de Google/BSG decompiladas.

No añadas árboles decompilados, smali, DEX, class, cachés, fotos ni trazas a Git. El APK conservado es una excepción binaria explícita de Git LFS. El historial publicado de GCam se reescribió para retirar los smali independientes: vuelve a clonar y no fusiones ramas antiguas. Clones, forks y URLs de commits en caché pueden conservar copias anteriores; [GitHub explica estos límites](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository).
