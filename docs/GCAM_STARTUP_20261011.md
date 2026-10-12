# Arranque de GCam: revisión del 11 de octubre de 2026

**Informe histórico de la investigación inicial.** Para el estado posterior,
consultar [revalidación del módulo GCam 0.2.0](GCAM_STARTUP_CURRENT.md).

**Resultado de esta etapa: el problema de arranque frío sigue pendiente.** No se obtuvo
una mejora reproducible con los cambios probados. No se instaló un APK
modificado ni se publicó un módulo de rendimiento. Las preferencias de ensayo
se restauraron y ART volvió a `speed-profile`. La primera presentación y el
indicador de controles no deben confundirse con una cámara lista para fotografiar.

## Alcance y entorno

Se revisaron arquitectura, documentación y manifests del módulo vigente,
los estudios anteriores de apertura, Top Shot, preview y RAW, los scripts
asociados, las preferencias actuales y los logs de nuevas aperturas. No se
revalidaron todos los experimentos archivados ni todos los modos de captura.
Se trabajó exclusivamente con ADB y root APatch, sin ARTEMIS.

- X6810-GL, Android 16 GSI; un único dispositivo ADB autorizado.
- BSG `com.android.MGC_9_7_047`, versión `9.7.047.702121536.18`.
- APK instalado y extraído: SHA-256
  `132e18273b3aafdb93e851f5db88156bd4f82c5032ad8de6594fa5a49ea6fe89`.
  El APK conservado en septiembre tiene otro hash; su decompilación sólo se
  usó como referencia. Se extrajeron clases clave del APK actual con JADX.
- Módulo principal `x6810_raw12mp`, v001. Los hashes de metastore y policy
  montados coincidieron con el módulo local: `bafeda846d6d6b81361487a6fa265ee4c70d6b085ce5520d0bd727b077d55d68`
  y `d3bfa9aab5d43af352a3bf717ff4b399cad6744ccc2c548ef8ae4650f3635ad2`.
- También está instalado `x6810_camera_ros` 0.3.0 experimental, con cambios
  en AI Moon/SenseSR y `debug.stagefright.c2inputsurface=0`. No se demostró
  una relación causal con el inicio; no se modificó.
- Preferencias observadas inicialmente: `device_key=blueline`,
  `pref_micro_mode=1`, `avc_profile_high_supported=false`. Se conservaron.

## Mediciones sin instrumentación Frida

Cada medición usa un proceso frío mediante `am force-stop`, conservando los
datos y cachés. Esto **no** equivale a primer arranque tras reinicio ni a
vaciar la caché de páginas. Se guardó logcat continuo; los pares no fueron
aleatorizados ni bastan para una prueba estadística de diferencias pequeñas.

| Condición | N | Mediana primera presentación | Mediana indicador de controles |
|---|---:|---:|---:|
| Controles consecutivos, sin `screencap` durante el inicio | 2 | 1703 ms | 2707,5 ms |
| ART `speed` en el APK actual | 3 | 1669 ms | 2750 ms |
| Gate de inicialización desactivado y UI a demanda desactivada | 2 | 1641,5 ms | 2754 ms |
| Sólo gate desactivado | 1 | 1774 ms | 2722 ms |
| Modo de rendimiento fijo temporal | 1 | 1888 ms | 3288 ms |

El indicador es el primer aviso `ModeSwitcher WAS ALREADY ENABLED!` relativo
al marcador ADB. No demuestra por sí solo que la preview tenga imagen ni que
el disparador acepte una captura. Incluye transporte y lanzamiento por ADB;
no es el TTFD definido por Android.

El control final, después de restaurar ajustes y retirar instrumentación,
dio 2026 ms de primera presentación; el HAL configuró en 46 ms. Sigue dentro
de la variabilidad observada y no acredita un arreglo de rendimiento.

La primera apertura de la sesión, con capturas de pantalla durante el inicio,
dio 3449 ms de primera presentación y 4953 ms para ese indicador. La captura
solicitada a 4 s aún mostraba preview negra. Las capturas tardaron hasta varios
segundos: esa observación no permite separar la carga de `screencap`, cachés y
variación del sistema. **La diferencia frente a aperturas posteriores no es
una mejora atribuible a un parche.**

Los HAL `configureStreams_3_6` nuevos tardaron decenas de milisegundos
(29–57 ms en varias aperturas examinadas). Los bloqueos del hilo principal
ocurrieron después de configurar. No hay evidencia para modificar los buffers
RAW, las resoluciones, los drivers de sensor ni los puentes de flash por este
problema.

Al volver desde Inicio se observó una actividad ya existente y `WaitTime` de
23–97 ms; otra recreación con proceso conservado dio 515 ms. Son mediciones de
reapertura, no de primera preview o primer disparo. Pulsar Atrás antes de acabar
una apertura produjo también un siguiente arranque frío; no se estableció su
causa. No se recomienda un servicio de permanencia a partir de estos datos.

## Ruta crítica actual

`atrace` informó un error al escribir `record-tgid`; Perfetto no pudo guardar
una traza útil porque `traced` se reiniciaba. Se extrajo el buffer de ftrace
directamente con root y se analizó localmente con el ejecutable oficial de
Perfetto v58.2, verificando su SHA-256 frente al manifiesto del distribuidor.
El importador informó 278 errores de parseo de líneas del vendor: los datos
son de diagnóstico, no una certificación completa de la traza.

Una apertura (primera presentación 1586 ms) dio:

| Bloque del hilo principal | Total | Ejecutando CPU | Listo/esperando CPU | Dormido o espera I/O |
|---|---:|---:|---:|---:|
| `bindApplication` | 898,62 ms | 604,31 ms | 232,03 ms | 62,28 ms |
| `CameraActivityController#initialize` | 937,88 ms | 673,24 ms | 36,23 ms | 228,41 ms |
| `UiWirer#wire` | 307,92 ms | 293,36 ms | 6,09 ms | 8,46 ms |

Los bloques tienen jerarquía: **no deben sumarse**. La misma traza registró
`cameraUiModule#inflate` de 334,34 ms y creación del controlador PHOTO de
415 ms. Confirma trabajo considerable de aplicación, pero no identifica un
único defecto que explique todas las aperturas de 5–6 s.

## Código y cachés de inferencia

En el DEX instalado, `hrs` fija `camera.on_demand_ui_wirer=true` por defecto.
`htj.o/p` consulta las preferencias explícitas mediante `com.a.ab/ad_mc`.
Por tanto, añadir otra vez el valor `true` no implica un cambio efectivo.
La prueba de gate/UI temprana sí escribió valores diferentes, pero no mejoró
el indicador de controles. Los valores experimentales quedaron ausentes.

Los logs iniciales también registran:

```text
Failed to updated cache: Unable to open file for writing: Is a directory
portrait_segmenter.cc:345] Could not initialize inference engine.
```

La ruta indicada era el directorio de caché externo de GCam. Es un error real
de esa apertura, pero apareció después del indicador de controles.
`NativePortraitSegmenterInterface.init` registra su implementación JNI en
`libgcastartup.so` a `0x23a9704` en el ELF extraído. La desensamblación confirma
que el argumento de caché es un `jstring` que pasa a la configuración nativa.

Una observación temporal con Frida recibió una ruta completa terminada en
`tflite_vakunov_multi-subject_2018-06-09.fb.enc.cache` y retorno `true` después
de 4567 ms. Otros intentos no observaron esa llamada; un intento por attach
entró en JNI pero no registró retorno antes de retirarse y detener GCam.
La instrumentación altera la ejecución y no respalda un benchmark. No se
demostró que el error de directorio corresponda a ese mismo argumento en
todas las rutas de inferencia. **No se sustituyó ningún argumento ni archivo
de caché, y no se convirtió el directorio en un archivo.**

No se justifica todavía un parche JNI de caché ni desactivar segmentación,
OpenCL, Top Shot o modelos para anunciar una mejora de inicio.

## Documentación oficial y decisión

Android distingue primera presentación y presentación completa, y recomienda
medir los bloques de inicialización antes de mover trabajo fuera del hilo
principal: [medición de arranque](https://developer.android.com/topic/performance/issues/launch-time)
y [análisis y optimización](https://developer.android.com/topic/performance/appstartup/analysis-optimization).
La inicialización a demanda y los perfiles Baseline/Startup son vías de
optimización de aplicación: [buenas prácticas](https://developer.android.com/topic/performance/appstartup/best-practices).

Forzar `speed` no crea un Startup Profile ni reorganiza el DEX. La prueba
actual no mejoró la preparación observable y se revirtió; véase
[configuración de ART Service](https://source.android.com/docs/core/runtime/configure/art-service).
La siguiente intervención en APK necesita una ruta de inicialización concreta,
validación de los tres sensores, captura y reprocesado, y una comparación
controlada de primera imagen y primer disparo. No hay evidencia actual para
publicar una modificación vendor de rendimiento.

## Comprobaciones y estado final

- Tres JPEG de diagnóstico nuevos se extrajeron y decodificaron en el host:
  3000×4000 píxeles, 12 MP, con contenido de la escena preparada. Esto verifica
  captura principal e integridad de esos archivos, no mejora de calidad ni
  funcionamiento de los otros sensores en esta sesión.
- `check_repository.py`: higiene y dos módulos completos validados.
- Utilidad reversible: `apply/restore` se ejercitó y verificó por lectura.
- APK, módulo RAW y ROS sin modificaciones persistentes de esta investigación.
  Gate/UI a demanda restaurados; `avc_profile_high_supported=false` conservado.
- ART `speed-profile`; modo de rendimiento fijo desactivado. Servidor Frida
  detenido, forwarding de diagnóstico retirado, trazado detenido y servicios
  de Perfetto iniciados durante el ensayo detenidos.
- Los archivos privados de esa sesión se guardaron en
  `dist/analysis/startup-20261011/` y se eliminaron durante la limpieza local
  de octubre de 2026. Las herramientas nuevas están aisladas en
  [gcam/startup](../gcam/startup/README.md).

El objetivo de una reducción verificable del arranque frío **no se alcanzó**.
