# GCam BSG 9.7 V32 - instalador APatch 0.7.0

Este instalador de sistema es opcional. Puedes instalar cualquier GCam externa
compatible como APK normal, sin él. El propietario confirma que V32 funciona
perfectamente con [el perfil recomendado](../../profiles/README.md), incluido
OIS del teleobjetivo probado y funcionando en Android 16 GSI. El XML se carga
manualmente y no se aplica al instalar el ZIP.

Módulo independiente para Infinix Zero X Neo X6810-GL. El instalador admite
Android 11 o posterior; sólo hay evidencia histórica en Android 16 GSI.
Incluye el APK original firmado proporcionado con `--apk`, sin modificar ni volver a firmar,
verificado por SHA-256:
`132e18273b3aafdb93e851f5db88156bd4f82c5032ad8de6594fa5a49ea6fe89`.

## Qué instala

- `system/priv-app/X6810GCam/X6810GCam.apk`: instalación automática en el siguiente arranque.
- Las 21 bibliotecas ARM64 del APK. Solo `libgcastartup.so` se sustituye por el arreglo verificado de caché del segmentador.
- XML de permisos runtime y lista privilegiada exclusivamente para `INSTALL_PACKAGE_UPDATES`, declarado por este APK.
- Concesión inicial de los 11 permisos runtime declarados, según la versión de Android.
- Acceso completo al almacenamiento (`MANAGE_EXTERNAL_STORAGE`), modificación de ajustes (`WRITE_SETTINGS`) y acceso a política No molestar.

Android concede los permisos normales y el permiso propio de firma. No se
conceden permisos ausentes del Manifest. El paquete queda como app privilegiada,
pero conserva su firma original: no adquiere la firma de la plataforma.

Si GCam ya está instalada con el mismo APK, Android puede mantenerla en
`/data/app` como `SYSTEM` + `UPDATED_SYSTEM_APP` + `PRIVILEGED`. Esto sigue siendo
una app de sistema. Se conservan sus datos y se monta únicamente el arreglo
nativo sobre su biblioteca original, verificando origen y propietario. No se
eliminan actualizaciones ni datos para forzar un cambio de ruta.

Esta versión usa el APK original: no aplica los parches DEX de inicio/panel de
0.5.0. Sí conserva el arreglo nativo de caché. Es independiente del módulo RAW.

## Construcción

Desde la raíz del repositorio:

```powershell
python scripts/build.py --apk /ruta/MGC_9.7.047_V32_MGC.apk
```

El constructor verifica el APK, todas las bibliotecas, ambas listas de permisos
y la integridad del ZIP. El instalador rechaza una versión instalada diferente.

## Instalación y diagnóstico

Instala el ZIP desde APatch y reinicia. No requiere instalar GCam manualmente.
El primer arranque puede tardar durante la compilación ART; los permisos se
configuran antes y no dependen de su éxito. La compilación completa solo se
repite si cambia la ruta, el payload o la compilación de Android.

En `/data/adb/modules/x6810_gcam_startup/`:

- `permissions-status.txt`: concesiones y verificación del permiso privilegiado.
- `status.txt`: hashes, modo activo y resultado de optimización.
- `.permissions-granted`: se crea solamente al completar las concesiones.

Las concesiones se hacen una vez por versión/UID/SDK para respetar revocaciones
posteriores. Si quieres repetirlas, elimina `.permissions-granted` y reinicia.
La automatización inicial apunta al usuario principal (0).

Para retirar el overlay, desactiva/elimina el módulo y reinicia. Si existía una
instalación en `/data/app`, queda disponible; una instalación exclusivamente
suministrada por el módulo deja de estar disponible. Los accesos especiales
concedidos no se revocan automáticamente al retirar el módulo: pueden retirarse
desde Ajustes. No uses `uninstall-system-updates` para cambiar la ruta sin un
respaldo: puede eliminar los datos.

## English

APatch 0.7.0 installs the original signed BSG 9.7 V32 as a privileged system app,
with all 21 ARM64 libraries and the verified native segmenter cache fix. It
grants declared runtime permissions, the allowlisted `INSTALL_PACKAGE_UPDATES`
permission, all-files access, write-settings access, and DND policy access.
Existing same-version installations and app data are preserved. Android may
retain the data APK as an updated privileged system app. Original APK signature
is preserved; earlier modified-DEX optimizations are not included. Install the
ZIP and reboot. User 0 is supported; subsequent user revocations are respected.
