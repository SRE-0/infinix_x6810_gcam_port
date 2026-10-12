# Instalación

Construye con `python scripts/build.py --apk /ruta/al/APK-original.apk`, verifica
SHA256SUMS e instala `x6810-gcam-system-0.7.0.zip` desde APatch. Reinicia para que
PackageManager escanee el overlay priv-app. El constructor exige el APK original
firmado y la biblioteca nativa de caché exacta. No instala un APK experimental
refirmado ni aplica todas las modificaciones DEX de los ensayos antiguos.

El módulo concede permisos runtime declarados y accesos especiales, conserva
datos existentes y comprueba hashes del APK instalado. Revisa
[estado del módulo](GCAM_SYSTEM_070.md) para la lista y sus efectos.
Desactiva/elimina `x6810_gcam_startup` y reinicia para retirar el overlay.
Los datos de usuario existentes no se borran automáticamente.

Sólo hay evidencia histórica en Android 16 GSI; los paquetes reorganizados no
se probaron en hardware en esta sesión. Android 11 requiere validación del APK,
permisos, ABI y arranque. El XML V18 en `profiles/` es opcional y no configura
automáticamente V32.

Para RAW/OIS/flash instala una variante del
[otro proyecto](https://github.com/SRE-0/infinix_x6810_raw) por separado.
