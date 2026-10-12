> Actualización 0.7.0: instalador privilegiado con APK original firmado, 21
> bibliotecas ARM64, arreglo nativo de caché, permisos runtime, lista privilegiada
> y accesos especiales. Sustituye las variantes 0.6.x. No incluye los parches DEX
> de 0.5.0. Consulta [el módulo vigente](../gcam/apatch-startup/README.md) y
> [la verificaci?n 0.7.0](GCAM_SYSTEM_070.md). El contenido inferior es histórico.

# Estado vigente del arranque de GCam — 12 de octubre de 2026

**Versión vigente del módulo: 0.6.0.** Instala el APK BSG 9.7 V32
optimizado en `/system/app/X6810GCam`, incluye la biblioteca nativa y concede
los 11 permisos runtime declarados, manteniendo las concesiones revocables. La
optimización de arranque de 0.5.0 se conserva.

**Verificación ADB en X6810-GL / Android 16:** PackageManager informa la ruta
de sistema, la marca `SYSTEM` y los 11 permisos runtime concedidos; el servicio
APatch confirma la compilación ART y los hashes del APK y de la biblioteca.
La comprobación de vista previa/captura queda pendiente de desbloquear el
teléfono después del reinicio.

La optimización de 0.5.0 conserva las pestañas y suscripciones visuales
del panel PHOTO diferidas hasta la primera apertura. Comparación ABBA: enlace
de UI 388 → 338 ms de mediana; disponibilidad conjunta 2,53 → 2,44 s de promedio
(seis aperturas por variante; la mejora de medianas es menor). Ver
[implementación, validación y estado de ML/microvideo](GCAM_PANEL_OPTIMIZATION_20261011.md).
El [cuaderno completo del laboratorio](GCAM_STARTUP_LAB_NOTEBOOK_20261012.md)
reúne cómo se detectaron los defectos, la preparación ADB/APatch y los ensayos
que se descartaron o quedaron pendientes.

**Actualización 0.4.0**, con caché nativa del segmentador corregida.
Mantiene el APK 0.3.0 y añade una instrucción nativa modificada. Comparación
ABBA: `initSegmenter` 4109 → 776 ms. La llamada empieza después de la vista
previa y del disparador; no se atribuyen las variaciones de apertura al parche.
Instalado y activo desde `modules_update`, sin reinicio. Ver
[corrección, recuperación y mediciones](GCAM_SEGMENTER_CACHE_FIX_20261011.md).

**Actualización 0.3.0:** se corrigió la extracción repetida del ELF de 39 MB.
Diez aperturas por variante dieron mediana TTID 1584.5 → 1429.5 ms y evento de
disparador habilitado 2571.589 → 2408.601 ms. Se instaló mediante APatch y se
activó sin reiniciar, por indicación del usuario. La versión está en
`modules_update`; su promoción tras reinicio queda pendiente. Ver
[implementación y validación del CRC](GCAM_CRC_FIX_20261011.md).
**Ajuste adicional:** registro continuo propio de BSG desactivado mediante
`pref_disable_log_key=1`. Ensayo ABBA: TTID 1625 → 1508 ms, vista previa
−126 ms desde onCreate; disparador solo −17 ms. Foto principal verificada.
Ver [segunda revisión y pendientes](GCAM_REMAINING_REVIEW_20261011.md).
El resto de este documento conserva la revalidación histórica de 0.2.0.

Se revisó el proyecto y se revalidó por ADB el módulo independiente
`x6810_gcam_startup` 0.2.0 para BSG `com.android.MGC_9_7_047` en X6810-GL,
Android 16 GSI. Esta sesión no usó ARTEMIS. Los informes anteriores conservan
sus resultados históricos; no describen todos el mismo APK ni la misma etapa.

## Diagnóstico y alcance del cambio

La ruta crítica de aplicación incluye el sondeo síncrono de hasta 250 IDs,
la construcción repetida de seis listas de perfiles de vídeo para PHOTO y
la creación de filas del panel de opciones oculto. Los ensayos previos
identificaron esas rutas en smali y mediante eventos/trazas. Los frames del
sensor llegan antes de terminar el controlador y la interfaz de GCam.

La solución existente y revalidada conserva:

- Sondeo limitado a IDs 0–5, específico de los seis dispositivos HAL del X6810.
- Caché por invocación de `hir.J`, confinada al hilo y retirada también ante
  excepciones. Reutiliza consultas de perfiles sin cambiar sus filtros.
- Filas PHOTO diferidas hasta abrir el panel por toque, gesto o accesibilidad;
  su estructura, estado y callbacks siguen conectados al inicio.
- Compilación ART `speed`, comprobando éxito y restaurando ante fallo.

La primera apertura del panel ejecuta el trabajo diferido en el hilo UI.
No se ha demostrado seguro trasladar todo `inflate`/`wire` a un worker.
El ensayo anterior de precalentamiento de perfiles en un worker no mejoró
consistentemente el disparador y se descartó.

Se compararon todas las entradas del APK original y la release: sólo cambian
`classes.dex` y `classes2.dex`; no se añaden ni eliminan entradas. Bibliotecas
nativas, recursos y Manifest coinciden. La auditoría está en
`dist/analysis/gcam-current-review-20261011/apk-entry-audit.json` (archivo privado eliminado en la limpieza local de octubre de 2026).

Original SHA-256: `132e18273b3aafdb93e851f5db88156bd4f82c5032ad8de6594fa5a49ea6fe89`.
Release SHA-256: `628012f407d7df89b6d7064cc5be6e103d4a0652de7123ddddd4a2295b17759d`.

El metastore publica RAW y resoluciones; pipelinepolicy normaliza la frontal
binned y el mínimo de buffers; HAL3A/CameraService contienen los puentes OIS y
flash. Sus funciones son distintas del trabajo DEX medido. Las configuraciones
HAL previas de decenas de milisegundos no justifican cambiar esas bibliotecas
para este retraso. No se cambiaron preferencias ni parámetros fotográficos.

## Documentación oficial y comparación con otras cámaras

Android distingue TTID de TTFD y recomienda medir, reducir inicialización
innecesaria y volver a medir. Un evento interno de preview no acredita el
instante óptico de presentación ni `reportFullyDrawn`:
[medición](https://developer.android.com/topic/performance/issues/launch-time),
[optimización](https://developer.android.com/topic/performance/appstartup/analysis-optimization).

El código público de la cámara AOSP usa apertura asíncrona con callback y
comprueba el ciclo de vida al recibir la cámara; carga la galería con callback
y crea la barra de deshacer al primer uso. Son ejemplos verificables de
coordinación y trabajo a demanda, no evidencia sobre el código privado de
Samsung o Xiaomi ni una comparación de tiempos con este GCam:
[CameraActivity](https://android.googlesource.com/platform/packages/apps/Camera2/+/a0abba23dfac80ef47aa32053e6aec6e487fb1ef/src/com/android/camera/CameraActivity.java).

Para fabricantes, AOSP documenta parámetros de sesión y consultas de
reconfiguración que permiten preparar el pipeline y evitar reconstrucciones
innecesarias. Exigen soporte real HAL y selección cuidadosa de claves; añadir
tags arbitrarios no implementa la función. No se aplican aquí sin evidencia de
un cuello de botella de reconfiguración:
[parámetros de sesión](https://source.android.com/docs/core/camera/session-parameters).

La cámara nativa Transsion obtuvo TTID de 0,76–1,23 s en los ensayos históricos,
con el mismo HAL. Es una referencia de primera presentación, no prueba de que
ambas apps preparen las mismas funciones ni de primera captura equivalente.

## Reproducción y evidencia

El nuevo ensayo `review_current` compara caché+scan6 frente a 0.2.0, con las
mismas marcas internas, ART `speed` en ambos y secuencia A/B/B/A. Excluye un
calentamiento por bloque y mide cuatro aperturas por variante mediante
`force-stop`. No borra datos/cachés ni ejecuta screenshots durante el inicio.
Filesystem caliente, muestra pequeña, sin control de DVFS/temperatura.

```powershell
python gcam/apk-analysis/run_lazy_options_benchmark.py --serial SERIAL --directory dist/analysis/gcam-lazy-options-20261011 --module-dir /data/adb/modules_update/x6810_gcam_startup --prefix ETIQUETA_NUEVA --runs 2 --trial-variant lazy-options-v2 --compile-mode speed
python gcam/apk-analysis/summarize_profile_trials.py dist/analysis/gcam-lazy-options-20261011 --prefix ETIQUETA_NUEVA
```

Después de promover el módulo por reinicio, usar `--module-dir
/data/adb/modules/x6810_gcam_startup`. El runner restaura la release en `finally`.
No reutilizar etiquetas de evidencia existentes.

Los cambios no acreditan mayor calidad fotográfica. La verificación de captura
y el arranque tras reinicio se documentan aparte de los indicadores de timing.
Instrucciones de construcción/restauración:
[módulo APatch](../gcam/apatch-startup/README.md).

## Resultado de la repetición actual

Ocho corridas completas, sin exclusiones, FATAL EXCEPTION ni ANR registrado.
Medianas desde marcador ADB salvo controlador y TTID:

| Métrica | Caché+scan6 | 0.2.0 | Diferencia |
|---|---:|---:|---:|
| Evento de preview de Activity | 2182,532 ms | 2054,169 ms | −128,363 ms (5,9 %) |
| Disparador habilitado | 2162,322 ms | 2009,206 ms | −153,116 ms (7,1 %) |
| Inicialización del controlador | 683,677 ms | 544,702 ms | −138,975 ms |
| TTID | 1205,5 ms | 1208,5 ms | +3,0 ms |
| Activity estable | 2820,198 ms | 2640,877 ms | −179,321 ms |

El cambio afecta a la preparación posterior, sin mejora de TTID en esta muestra.
Los rangos de preview se solapan parcialmente: control 2075–2321 ms,
0.2.0 1929–2143 ms. El disparador: control 2108–2209 ms, 0.2.0 1983–2035 ms.
No se acredita significancia estadística ni un límite máximo universal.

Los JSON completos y las mediciones crudas estaban en `dist/analysis/`; se
eliminaron durante la limpieza local de octubre de 2026. Esta sección conserva
los resultados resumidos. Para obtener datos nuevos, vuelve a ejecutar el
benchmark con una etiqueta distinta y un dispositivo conectado.

La release quedó restaurada y compilada al terminar el runner. Una captura
fría con input solicitado a 2,3 s, enviado entre 2,300 y 2,489 s, produjo un
JPEG nuevo observado a 7,323 s y extraído al host. Ese intervalo incluye
procesamiento y posible cola de input; no prueba disponibilidad exacta a 2,3 s.
El metastore y policy activos coincidieron con los hashes del módulo RAW v001.

## Reinicio real: persistencia verificada, apertura inicial pendiente

Se reinició el dispositivo por ADB. APatch promovió la carpeta de actualización
a `/data/adb/modules/x6810_gcam_startup`; su servicio montó automáticamente el
payload correcto, sin ejecución manual de `apply`. Los hashes de metastore y
policy siguieron coincidiendo con v001.

El primer lanzamiento recogido tras desbloquear ocurrió mientras el servicio
seguía en `cmd package compile -m speed -f`: ART informó `verify` y la primera
presentación tardó **6668 ms**. La captura solicitada a 8 s, recibida entre 8,000
y 10,103 s, mostró controles sobre una preview negra. La configuración HAL
duró 89 ms. No se puede atribuir toda esta demora a la compilación concurrente
sin una comparación controlada; demuestra que la optimización de aperturas
posteriores **no resuelve todavía la primera apertura tras reiniciar**.

Se observó el proceso de compilación real (ejecutable `linker` con argumentos
DEX/`--compiler-filter=speed`, hijo de `artd`). Al finalizar, `status.txt`
registró `Success` y el hash activo, y ART pasó a `speed reason=cmdline`.
Persistencia y finalización de compilación verificadas, sin tiempo máximo de
preparación garantizado. No lanzar el benchmark antes de esa finalización.

Un intento posterior de captura temprana (`capture-after-reboot`) no produjo
JPEG y además se solapó al final con la selección del telefoto; se conserva
como intento fallido, no se utiliza como medida comparativa de disponibilidad.
Las capturas funcionales por sensor se realizaron después por separado.

Los archivos privados (`device-after-reboot.txt`, trazas y capturas) se
eliminaron de `dist/analysis/` durante la limpieza local de octubre de 2026.
Este informe conserva el resumen de la sesión.

## Comprobación funcional final

Tras completar ART se extrajeron JPEG nuevos y se decodificaron en el host:

| Sensor | Dimensiones | Archivo observado tras input/captura warm |
|---|---|---:|
| Principal | 3000×4000 | 5,734 s desde inicio del probe |
| Frontal | 1744×2320 | 4,353 s |
| Telefoto | 2448×3264 | 16,117 s |

Los probes warm verifican funcionamiento, no apertura ni mejora de procesamiento.
La escena y el enfoque no estaban controlados. El telefoto más lento no se
atribuye al parche sin comparación; no se demuestra mejora de calidad o enfoque.
No se revalidaron DNG, OIS, SINGLE/TORCH, todos los modos ni estrés prolongado.

La apertura posterior `after_compile_1` dio TTID **2465 ms** sin screenshots
concurrentes; es un dato aislado posterior al reinicio y no sustituye el A/B/B/A.
La primera apertura del panel PHOTO después de ese arranque mostró General,
Pro, flash, Google AWB, HDR+, Top Shot, timer, ratio y foco en XML fresco.
Se cerró el panel y se dejó PHOTO con la principal seleccionada.

Preferencias leídas: `device_key=blueline`, `pref_micro_mode=1`,
`avc_profile_high_supported=false`. No se escribieron preferencias.
El módulo 0.2.0 ya existente sigue activo; esta revisión no introduce otro
parche APK/vendor ni integra el worker descartado. Corrige documentación
desactualizada y aporta una nueva repetición y la validación de reinicio.
La mejora incremental se reprodujo con sistema preparado; la primera apertura
tras reinicio requiere trabajo adicional antes de declararla resuelta.
