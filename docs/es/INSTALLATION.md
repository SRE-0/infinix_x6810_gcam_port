[English](../INSTALLATION.md) | **Español**

# Instalación: GCam externa o módulo de sistema opcional

Puedes instalar cualquier GCam externa compatible como APK de usuario, sin el
módulo GCam de sistema. El módulo RAW/OIS/HD48 y su variante flash funcionan al
nivel de Camera2/vendor y no exigen una app concreta. La compatibilidad depende
del port y Android: no se afirma que todas las APK existentes funcionen.

La [MGC_9.7.047_V32_MGC.apk](https://1-dontsharethislink.celsoazevedo.com/file/filesc/MGC_9.7.047_V32_MGC.apk),
paquete `com.android.MGC_9_7_047`, funciona perfectamente con
[el perfil recomendado V32](../../profiles/README.md), en las pruebas realizadas en Android 16 GSI. OIS del teleobjetivo también está probado y
funciona correctamente. Carga el XML desde la gestión de configuraciones BSG;
guardar tu configuración previa permite volver a ella.

## Instalación de sistema opcional

Construye con `python scripts/build.py --apk /ruta/al/APK-original.apk`, verifica
SHA256SUMS e instala `x6810-gcam-system-0.7.0.zip` desde APatch. Reinicia para que
PackageManager escanee el overlay priv-app. El constructor exige el APK original
V32 firmado y la biblioteca nativa de caché exacta; no admite otra GCam, a
diferencia de la instalación externa manual.

El módulo concede permisos runtime declarados y accesos especiales, conserva
datos existentes y comprueba hashes del APK instalado. Revisa
[estado del módulo](../GCAM_SYSTEM_070.md) para la lista y sus efectos. El XML V32
se entrega como archivo separado y se importa manualmente; no se aplica al boot.
Desactiva/elimina `x6810_gcam_startup` y reinicia para retirar el overlay.
Los datos existentes no se borran automáticamente y los accesos especiales
concedidos pueden seguir activos: revócalos desde Ajustes si lo deseas.

La evidencia real corresponde a Android 16 GSI. El instalador admite SDK 30+,
pero Android 11 requiere validación del APK, permisos, ABI y arranque. Los
paquetes reorganizados no se probaron de nuevo en hardware en esta sesión.
Para RAW/OIS/HD48/flash instala una variante del
[otro proyecto](https://github.com/SRE-0/infinix_x6810_raw) por separado.
