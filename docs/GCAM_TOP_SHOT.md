# Top Shot en BSG GCam 9.7: diagnóstico y corrección

Investigación: 26 de septiembre de 2026. Confirmación del usuario: 27 de septiembre de 2026.

**Resultado:** el usuario confirmó que Top Shot funciona correctamente y sin cierres inesperados después de aplicar una preferencia de compatibilidad del codificador AVC. La corrección es de GCam; el módulo RAW permanece en v0.11.0.

## Entorno observado

- Infinix Zero X Neo X6810, Android 16, root accesible mediante APatch.
- Paquete: `com.android.MGC_9_7_047`.
- `versionName`: `9.7.047.702121536.18`; `versionCode`: `68097556`.
- Principal S5KGM1ST, telefoto OV08A10 y frontal HI1631Q.
- Bibliotecas montadas y verificadas por SHA-256:

| Biblioteca | SHA-256 observado |
|---|---|
| `libmtkcam_metastore.so` | `a05f038d7e638f597f751750cafc0e0c9d788be85588e52afbfeff9e583759d5` |
| `libmtkcam_pipelinepolicy.so` | `d3bfa9aab5d43af352a3bf717ff4b399cad6744ccc2c548ef8ae4650f3635ad2` |

## Cambio exacto

Archivo privado de preferencias que se editó con root:

```text
/data/user/0/com.android.MGC_9_7_047/shared_prefs/com.android.MGC_9_7_047_preferences.xml
```

Se añadió dentro de `<map>`, antes de `</map>`, una única preferencia:

```xml
<boolean name="avc_profile_high_supported" value="false" />
```

La clave **no existía** en el XML anterior: GCam resolvía su valor mediante sus valores predeterminados/perfil de dispositivo. No se sustituyó un `true` explícito. Debe ser un elemento `boolean`, no un `string`.

La selección de Top Shot ya estaba activada (`pref_micro_mode` tenía el valor de cadena `2`); no se cambió. Tampoco se cambiaron HDR+, resoluciones, Surface list, formatos RAW, propiedades del sistema, APK, bibliotecas, número de buffers ni módulo APatch.

## Causa y evidencia

La interfaz mostraba Top Shot activado, pero una captura de referencia guardada durante la investigación era un JPEG sin marcador MP4 `ftyp` ni etiquetas `MotionPhoto`/`MicroVideo`. El log identificó el fallo previo al guardado:

```text
ACodec: [OMX.MTK.VIDEO.ENCODER.AVC] configureCodec returning error -61
MediaCodec: Codec reported err 0xffffffc3/NOT_ENOUGH_DATA
CAM_kea: Prewarm of microvideo encoder failed... will try again later!
CAM_kbh: Cannot get final shutter timestamp from microvideo as it failed to start!
```

La inspección del APK instalado permitió seguir esta ruta, cuyos nombres ofuscados son específicos de esa compilación:

1. `hrs.X` representa `avc_profile_high_supported`.
2. `htj.p(...)` consulta la preferencia explícita antes del valor predeterminado.
3. `kee.b()` y ramas de `ked` pasan ese booleano a `kgs.a(...)`, que construye el `MediaFormat` del microvídeo.
4. Para AVC y booleano verdadero, `kgs.a(...)` fija `profile=8` y `level=32768` (AVC High, nivel 5.1). Con falso, omite ambos campos, dejando al codificador/framework elegir sus valores predeterminados.

El framework Android verifica el perfil y nivel solicitados contra los anunciados por el componente OMX al configurar AVC; esta ruta puede rechazar la configuración antes de crear la superficie de entrada. Referencia: [ACodec en AOSP](https://android.googlesource.com/platform/frameworks/av/+/master/media/libstagefright/ACodec.cpp).

**Diagnóstico:** la solicitud explícita de perfil/nivel de GCam era incompatible con la ruta AVC de este dispositivo. No se demostró que todo uso de AVC High sea imposible: el experimento retiró conjuntamente perfil y nivel, sin probarlos por separado.

Después de añadir la preferencia y relanzar GCam, los logs cambiaron a:

```text
ACodec: setupAVCEncoderParameters with [profile: Baseline] [level: Level41]
ACodec: setupVideoEncoder succeeded
```

Esto verifica la corrección de la configuración del codificador. Posteriormente el usuario confirmó el funcionamiento de Top Shot sin cierres. No se completó una matriz automatizada de capturas finales por lente ni una extracción/decodificación de cada MP4 generado; la confirmación funcional final proviene del usuario.

## Cómo se aplicó en esta sesión

1. Se detuvo únicamente GCam mediante `adb -s SERIAL shell am force-stop com.android.MGC_9_7_047`.
2. Se leyó el XML con `su -c cat` y se guardó una copia local previa.
3. Se insertó la línea anterior antes de `</map>` y se comprobó que el XML seguía siendo válido.
4. Se transfirió el XML editado mediante `adb push` a `/data/local/tmp/topshot-prefs.xml`.
5. Se sobrescribió el contenido del archivo existente mediante una redirección ejecutada **dentro de `su -c`**, conservando el inode y sus permisos/contexto:

   ```text
   adb -s SERIAL shell "su -c 'cat /data/local/tmp/topshot-prefs.xml > /data/user/0/com.android.MGC_9_7_047/shared_prefs/com.android.MGC_9_7_047_preferences.xml'"
   ```

6. Se releyó el archivo y se comparó con el editado, normalizando los retornos de carro introducidos por la salida ADB. Se confirmó `avc_profile_high_supported=false`.
7. Se relanzó GCam mediante `am start -W -n com.android.MGC_9_7_047/com.android.camera.CameraLauncher` y se compararon los logs.

Un primer intento de escritura dejó la redirección fuera de `su -c` y falló por permisos; no modificó el archivo. El intento corregido es el descrito arriba.

Se reinició después el teléfono para investigar la inestabilidad de memoria. **El codificador ya había configurado correctamente antes de ese reinicio**: no hay evidencia de que reiniciar todo el teléfono sea necesario para este ajuste. La preferencia persistió después del arranque.

## Reproducir y revertir

Se incluyó [configure_mgc_topshot.py](../scripts/configure_mgc_topshot.py) para aplicar únicamente esta preferencia, crear un respaldo, verificar la lectura y restaurar el valor previo sin sustituir las demás preferencias actuales. Usa Python estándar, ADB y root; no utiliza ARTEMIS.

```powershell
python scripts/configure_mgc_topshot.py status --serial SERIAL --backup-dir dist/topshot-backup
python scripts/configure_mgc_topshot.py apply --serial SERIAL --backup-dir dist/topshot-backup
```

El script deja GCam detenida: abrirla normalmente después. Para revertir una aplicación realizada con ese script:

```powershell
python scripts/configure_mgc_topshot.py restore --serial SERIAL --backup-dir dist/topshot-backup
```

El respaldo debe corresponder a ese dispositivo y a la aplicación original del cambio. Si se ejecuta `apply` cuando el ajuste ya es `false`, el respaldo registra `false`; `restore` no lo eliminará. Para deshacer **el cambio original de esta investigación**, detener GCam, eliminar únicamente el elemento `boolean` indicado y volver a abrirla, porque originalmente la clave estaba ausente. No cambiarlo a `true` como supuesto equivalente universal.

La modificación de esta sesión se realizó con comandos ADB/Python antes de crear la utilidad. Se verificó la ayuda y la consulta `status` de la utilidad; sus operaciones `apply`/`restore` no se ejercitaron sobre el dispositivo para evitar alterar el estado funcional confirmado por el usuario.

Importar otra configuración o borrar los datos de GCam puede eliminar el ajuste. La instalación del módulo v0.11 no lo aplica automáticamente. Esta observación no garantiza el mismo comportamiento en otras versiones de GCam.

## Memoria y ARTEMIS

Durante la investigación Android registró cierres de GCam por `LOW_MEMORY`, errores de scrcpy y aproximadamente 3,8 GB de ION en una instantánea global. ARTEMIS también agotó la cuota de su modelo y su tarea autónoma se canceló; se continuó por ADB. El usuario indicó que las pruebas previas sin ARTEMIS no presentaban esos cierres y que ahora Top Shot funciona sin ellos.

No se hizo una comparación controlada con/sin ARTEMIS ni v0.10/v0.11. Por tanto, **la relación causal entre ARTEMIS y la presión de memoria queda como hipótesis del usuario, no como hecho demostrado**. Tampoco se atribuye a v0.11 una fuga de memoria. Cuatro buffers RAW16 adicionales de 4000×3000 representan unos 96 MB decimales de datos, antes de alineación y estructuras; este cálculo no es una medición del consumo completo del pipeline.

Por instrucción del usuario, se dejó de utilizar ARTEMIS. No se redujeron los seis buffers de v0.11 para resolver Top Shot.

## Evidencias y revisión del proyecto

Los archivos privados de la sesión se guardaron originalmente bajo
`dist/analysis/topshot-20260926/` y se eliminaron durante la limpieza local de
octubre de 2026. Este informe conserva el resumen técnico; no redistribuyas XML
privados, logs, capturas ni datos del dispositivo.

La revisión cubrió arquitectura, evolución de los parches, manifests, instalador y plantilla. Se ejecutaron satisfactoriamente:

- `verify_v011_raw_buffers.py`: 12 rutas del hook/setter, reproducción exacta del parche y preservación del parche frontal.
- `test_v08_installer_host.py x6810_raw_v011 x6810_raw_v010_from_v011_rollback`: 32 casos de instalación/rollback en host; permisos simulados.
- `test_module_template.py`: plantilla de los 15 módulos.
- `check_repository.py`: higiene del repositorio.

Estos controles respaldan la consistencia del proyecto; no sustituyen una certificación Camera2/CTS ni constituyen una prueba de ausencia de fugas durante uso prolongado.
