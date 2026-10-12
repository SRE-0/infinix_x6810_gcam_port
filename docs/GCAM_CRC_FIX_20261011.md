# Corrección de CRC de la biblioteca de arranque

La versión 0.3.0 del módulo independiente `x6810_gcam_startup` conserva los
cambios de 0.2.0 y corrige la validación del ELF extraído de
`assets/QrQJbYT787QDr7Co`. El archivo derivado `codec_hevc.lck` tiene
38953640 bytes. El cargador transforma sus tres primeros bytes a `7f 45 4c`,
por lo que su CRC real no coincide con el del asset enmascarado.

## Implementación

Se sustituye únicamente la primera llamada a `bc(File)` en
`com.android.app.Application.b()` por `x6810ElfAssetCrc(File, ZipEntry)`.
El helper verifica tamaño y cabecera ELF, procesa tres ceros y el cuarto byte
`46` en CRC32, y después lee todo el contenido restante en bloques de 8192 bytes.
El CRC resultante corresponde a la representación original del asset.

Un tamaño o cabecera incorrectos, o un error de lectura/cierre, devuelve `-1`,
que no puede coincidir con un CRC32 válido. Un cambio en el contenido restante
también invalida la copia. Se conserva la extracción y carga original; no se
omiten verificaciones ni se añade una marca que permita reutilizar datos sin
leerlos. `bc(File)` y la segunda extracción ZIP permanecen intactos.

El cambio evita descomprimir y escribir de nuevo unos 39 MB por apertura normal.
Todavía lee ese archivo para verificar su CRC. No cambia el contexto de JNI,
el hilo de carga ni el formato del ELF. La escritura de recuperación sigue
usando el comportamiento original de la aplicación.

## Identidad y alcance

- Base 0.2.0: `628012f407d7df89b6d7064cc5be6e103d4a0652de7123ddddd4a2295b17759d`.
- Payload 0.3.0: `d4ec771a9114778f1689ee256debf128e824e1e305de499e1580667e65d227d7`.
- Cambia solamente `classes.dex` respecto a 0.2.0.
- El main DEX pasa de 65461 a 65463 referencias a métodos.
- La reconstrucción sin parche produce un DEX idéntico al de la base.
- Se mantienen Manifest, recursos, otros DEX y bibliotecas del APK.
- El módulo RAW y las preferencias de GCam no se modifican.

## Recuperación verificada en el teléfono

Se probaron seis situaciones con la variante de distribución y compilación
ART `speed`, mediante ADB y root APatch:

| Situación | Resultado |
|---|---|
| Copia válida | Se reutiliza; tamaño, inode y mtime no cambian |
| Archivo ausente | Se extrae de nuevo y carga |
| Primer byte de cabecera dañado | Se detecta y recupera |
| Byte de contenido en offset 4 alterado, mismo tamaño | Se detecta y recupera |
| Archivo truncado a 4096 bytes | Se detecta y recupera |
| Nueva apertura después de recuperación | Se reutiliza sin otra escritura |

En todos los casos el archivo final coincide con SHA-256
`fe4494b6fbb4424c302cc53ea387699e4d43dfa9d0ba0d1ac9c3fc952428de90`.
No se observaron FATAL EXCEPTION, VerifyError, UnsatisfiedLinkError ni ANR
en los registros de estas pruebas. Se guardó una copia verificada del archivo
derivado antes de inducir daño y se retiró al terminar las comprobaciones.
La preview de la variante de distribución se comprobó visualmente.

## Comparación A/B/B/A

Se midieron diez aperturas por variante, cinco por bloque, con un calentamiento
excluido en cada bloque. Ambas variantes usan los mismos hooks de diagnóstico,
la misma configuración y ART `speed`. Se fuerza el cierre del proceso; no se
borran datos ni cachés, y no se toman screenshots durante la medición.

| Mediana | 0.2.0 | CRC corregido | Diferencia |
|---|---:|---:|---:|
| TTID | 1584.5 ms | 1429.5 ms | −155.0 ms (9.8 %) |
| Marcador → onCreate | 951.0 ms | 817.5 ms | −133.5 ms |
| Marcador → primer frame recibido | 1649.911 ms | 1504.105 ms | −145.806 ms |
| Marcador → evento de preview de Activity | 2739.049 ms | 2527.004 ms | −212.045 ms (7.7 %) |
| Marcador → disparador habilitado | 2571.589 ms | 2408.601 ms | −162.988 ms (6.3 %) |
| Inicialización del controlador | 735.960 ms | 725.631 ms | −10.329 ms |
| UI wire | 391.722 ms | 393.127 ms | +1.404 ms |

La mejora está antes de la actividad; el trabajo de interfaz no cambia.
La versión anterior reescribe el ELF en 10/10 aperturas medidas; la nueva,
en 0/10. No hubo FATAL EXCEPTION ni ANR registrado en esas veinte aperturas.
Rango TTID: control 1534–1708 ms, parche 1400–1465 ms. Rango del disparador:
control 2495–2854 ms, parche 2353–2489 ms.

Es una muestra de un dispositivo, con filesystem caliente. Los tiempos desde
marcador incluyen transporte ADB y no son latencia de toque físico ni TTFD
óptico. No se fijaron DVFS ni temperatura; hay capturas de thermalservice antes
y después. No se acredita significancia estadística ni una reducción universal.

Datos: `crc_abba-results.json`, `crc_abba-summary.json` y
`measurements/` dentro de `dist/analysis/gcam-crc-20261011/`.

## Instalación y comprobación final

Se instaló `x6810-gcam-startup-0.3.0.zip` con APatch y se activó desde
`/data/adb/modules_update/x6810_gcam_startup/activate.sh`. El montaje verifica
el payload `d4ec771a…65d227d7` y ART `speed` terminó con Success. Por indicación
del usuario **no se reinició**: la promoción a `modules` y la activación automática
de esta versión tras reinicio no se verificaron.

La apertura final con el módulo instalado conservó el mtime del ELF. Dio TTID
1779 ms en una observación aislada con la variante de distribución; no es otra
comparación A/B ni sustituye las medianas instrumentadas. Se comprobó preview
y guardado de JPEG principal de 3000×4000, decodificado e inspeccionado visualmente.
El input se solicitó a 3 s del inicio, se envió entre 3.000 y 3.284 s y el archivo
final se observó a 8.092 s. Incluye procesado y sondeo; no demuestra TTFD ni
una mejora de calidad fotográfica. No se repitieron en esta corrección ensayos
RAW, flash, video ni las otras dos cámaras.

Estado y evidencia final: `final-module-status.txt`, `final-module-prop.txt`,
`module-cache-before.txt`, `module-cache-after.txt`, `module_030_final/` y
`photo-final/` en el directorio del ensayo.

## Reproducción

Los artefactos privados y mediciones se guardan en
`dist/analysis/gcam-crc-20261011/`. Partiendo de la extracción auditada:

```powershell
python gcam/apk-analysis/prepare_crc_trial.py dist/analysis/gcam-apk-20261011/apktool dist/analysis/gcam-full-audit-20261011/active.apk SALIDA_AISLADA
java -Xmx3072m -cp C:/Windows/apktool.jar gcam/apk-analysis/AssembleSmali.java SALIDA_AISLADA/smali SALIDA_AISLADA/crc-main.dex
python gcam/apk-analysis/repack_crc_trial.py dist/analysis/gcam-full-audit-20261011/active.apk SALIDA_AISLADA/crc-main.dex SALIDA_AISLADA/crc-release.apk
python gcam/apatch-startup/build.py SALIDA_AISLADA/crc-release.apk SALIDA_AISLADA/x6810-gcam-startup-0.3.0.zip
```

Los constructores rechazan sobrescrituras y la preparación verifica tanto la
huella del APK como la clase smali de origen. El APK reconstruido se usa mediante
montaje APatch; no es una actualización firmada para `adb install`.

El ensayo de recuperación reproducible es `verify_crc_device.py`: exige serial,
la huella exacta del payload de prueba y el ELF conocido. Modifica únicamente
ese archivo derivado, realiza copia de seguridad y restaura si una prueba falla.
No usarlo durante una captura ni sobre otra versión del APK.

El [análisis completo](GCAM_APK_FULL_AUDIT_20261011.md) describe el defecto y
otros candidatos. Esta corrección no modifica los modelos, codecs ni calidad
fotográfica; su objetivo es evitar trabajo repetido de arranque.
