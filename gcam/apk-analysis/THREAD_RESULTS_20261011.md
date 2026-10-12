# Pruebas de inicialización en segundo plano — 2026-10-11

Se construyeron y ejecutaron dos variantes del APK mediante ADB y root APatch.
La precarga de clases mostró una reducción modesta frente al control reconstruido:
107,5 ms en la mediana TTID y 223,5 ms en un indicador de controles. La precarga
adicional de fuentes no mostró mejora estable. **No se ha resuelto el tiempo
completo hasta poder fotografiar ni se trasladó todo el controlador a otro hilo.**
El APK original quedó restaurado, sin montaje de ensayo ni módulo permanente.

## Qué se puede separar

La traza anterior del APK original contiene `CameraActivityController#initialize`
937,88 ms, `setModuleFromMode PHOTO` aproximadamente 415 ms, `cameraUiModule#inflate`
334,34 ms y `UiWirer#wire` 307,92 ms. Son secciones anidadas; no deben sumarse.
La traza está en `dist/analysis/startup-20261011/rawtrace_current_01/startup.atrace`.

`glc.d()` llama a `jnr.w()`; el módulo PHOTO se obtiene mediante `jpq` y construye
`jpp`, con muchas dependencias que incluyen vistas, listeners y `HotshotController`.
Las rutas de opciones y UI usan comprobaciones de hilo principal (`pdh`, `qzm`).
Cambiar el executor de toda la cadena puede ejecutar esas operaciones fuera del
hilo requerido. Android especifica que las vistas no son seguras para acceso
concurrente y que el trabajo de UI corresponde al hilo principal.
[Documentación oficial de hilos](https://developer.android.com/topic/performance/threads).

Por ello, este ensayo separa preparación de clases y recursos; conserva los
constructores de controladores, proveedores y todas las operaciones de vistas
en sus rutas originales. No elimina comprobaciones de hilo ni altera parámetros
de captura, OIS, buffers, sensores o bibliotecas MTK.

## Variantes

| APK | Modificación sobre el original |
|---|---|
| `control39.apk` | Reensamblado de `classes2.dex`, sin hook ni helper; controla los efectos de reconstrucción |
| `worker39.apk` | Hook al inicio de `CameraApp.onCreate()`; worker con prioridad Android 10 que precarga 46 clases con `Class.forName(name, false, loader)` |
| `fonts39.apk` | El mismo worker, más tres fuentes Google Sans mediante la rutina obfuscada `dwp.b()` de ResourcesCompat |

El worker no hace `join`, no publica vistas y no captura una Activity. En clases
se usa `initialize=false`: no ejecuta los inicializadores estáticos ni los
constructores. Si una precarga falla, la carga original sigue disponible.
Los 46 nombres se verificaron contra el smali extraído. Son dependencias generales
de inicialización, UI y varios modos; **no son una lista exclusiva del módulo PHOTO**.
En particular, `kkh`/`kkf` pertenecen a otras rutas de modos.

La variante de fuentes usa Context de Application, TypedValue independiente,
callback nulo y caché sincronizada. Esta variante sí puede inicializar clases
del cargador de fuentes: el texto inicial del log heredado «no static initialization»
describe sólo la precarga por `Class.forName(false)`, no la llamada a fuentes.
ResourcesCompat documenta que la carga bloqueante ejecuta trabajo en el hilo
llamante. [API oficial](https://developer.android.com/reference/androidx/core/content/res/ResourcesCompat),
[implementación AndroidX](https://android.googlesource.com/platform/frameworks/support/+/refs/heads/androidx-main/core/core/src/main/java/androidx/core/content/res/ResourcesCompat.java).

En los logs, PID 30779/TID 30816 y PID 31146/TID 31180 confirman el worker fuera
del hilo principal. La precarga de 46 clases termina en 0–1 ms en estas corridas.
Fuentes termina en 6–11 ms en las cuatro corridas incluidas; se registran tres
mensajes de fuente completada. No aparecieron `FATAL EXCEPTION`, ANR ni fallos
de precarga en los registros de las variantes válidas revisados.
Estos tiempos pequeños no explican por sí solos los 938 ms del controlador.

## Mediciones

Infinix X6810, Android 16 GSI, paquete `com.android.MGC_9_7_047`, mismo conjunto
de preferencias, escena iluminada y ART `speed-profile` forzado con resultado
`Success` después de cada intercambio. Apertura fría de proceso mediante
`am force-stop`, pausa de 2 s y `am start -W`; cachés de archivos calientes.
Se capturaron 8 s de logs por corrida, sin screenshots durante el benchmark.
Los bloques se intercalaron: control, clases, fuentes, control, clases, fuentes,
control, clases; original al inicio y al final, más dos corridas finales de
fuentes para sustituir un bloque cuya compilación no quedó confirmada. No hubo
reboot ni purga de datos.
Una lectura térmica mostró estado 0 y dispositivos de enfriamiento en 0;
no se midió temperatura individual en cada corrida.

| Variante | n | Mediana TTID | Rango TTID | Mediana indicador de controles |
|---|---:|---:|---:|---:|
| Original, referencia adicional | 3 | 1944 ms | 1630–2136 ms | 3201 ms |
| Control reconstruido | 6 | 1682 ms | 1616–1880 ms | 2838 ms |
| Clases en worker | 6 | 1574,5 ms | 1525–1644 ms | 2614,5 ms |
| Fuentes + clases | 4 | 1897 ms | 1612–2456 ms | 3213,5 ms |

Clases frente al control: **−107,5 ms TTID (6,4 %) y −223,5 ms en el indicador
de controles (7,9 %)**. Es una señal favorable en una muestra pequeña, con rangos
solapados; no se atribuye toda la diferencia al trabajo trasladado de 0–1 ms.
El control también difiere del original: no sería correcto atribuir la diferencia
original/worker íntegramente al hook. Faltan más alternancias y una traza comparada
antes de recomendar una integración permanente.

Fuentes tuvo aperturas de 1,6–2,5 s en el conjunto válido y medianas peores que
el control. Se conserva esa variación: no se afirma una causa específica ni una
mejora reproducible. No se recomienda esta variante.

| Corrida | TTID ms | Indicador controles ms |
|---|---:|---:|
| original_01 | 2136 | 3287 |
| control39_01 | 1880 | 3232 |
| control39_02 | 1616 | 2739 |
| worker39_01 | 1644 | 2897 |
| worker39_02 | 1609 | 2666 |
| fonts39_01, excluida | 2996 | 4378 |
| fonts39_02, excluida | 2970 | 4352 |
| fonts39_03, excluida | 2896 | 4423 |
| control39_03 | 1651 | 2858 |
| control39_04 | 1660 | 2781 |
| worker39_03 | 1568 | 2563 |
| worker39_04 | 1525 | 2528 |
| fonts39_04 | 1829 | 3011 |
| fonts39_05 | 1612 | 2720 |
| control39_05 | 1704 | 2836 |
| control39_06 | 1734 | 2840 |
| worker39_05 | 1530 | 2487 |
| worker39_06 | 1581 | 2681 |
| original_02 | 1944 | 3201 |
| original_03 | 1630 | 2727 |
| fonts39_06 | 1965 | 3416 |
| fonts39_07 | 2456 | 4034 |

`fonts39_01` y `fonts39_02` se excluyen porque se inició la compilación ART
mientras la primera aplicación del APK aún estaba pendiente; no se confirmó
que esa compilación operara sobre fuentes. No se utiliza ese bloque para
atribuir una regresión a las fuentes. Las corridas 04–07 sí se hicieron después
de completar el montaje y recompilar ART con éxito.
`fonts39_03` se excluye por haber iniciado la exploración UI de captura mientras
el colector aún estaba pendiente de recoger; se retiene por auditoría y no por
su resultado. `control_01` falló por un formato DEX inválido y no es una medición
de rendimiento: el escritor de apktool con API 35 emitió magic 041 y cabecera
clásica de 112 bytes, incompatible con ART. Se restauró el original y se corrigió
el ensamblador a DEX 039/API 28, igual al formato original. Todos los ensayos
`*39` compilaron y abrieron con ART.

TTID mide la primera pantalla, no la preview lista. El indicador se obtiene de
`ModeSwitcher WAS ALREADY ENABLED!` relativo al marcador ADB; es un proxy, no TTFD.
[Definiciones oficiales de apertura](https://developer.android.com/topic/performance/issues/launch-time).
No se utiliza esta tabla para afirmar que los 5–6 s originales se hayan reducido
en el mismo porcentaje.

## Preview y fotografía

En `worker39`, la preview principal se revisó visualmente. El proveedor de
métricas mostró frames principales RAW 4000×3000 y preview 1440×1080; los dumps
verificaron cámara 2 activa para telefoto con OIS `ON` y cámara 1 para frontal.
Se localizaron el disparador y los selectores por resource-id y bounds de
UIAutomator antes de actuar. Los JPEG siguientes se descargaron y se
decodificaron con System.Drawing; las resoluciones conservan los sensores.

| Variante/cámara | Archivo | Resolución JPEG |
|---|---|---:|
| Worker / principal | `PXL_20261011_142304491.jpg` | 3000×4000 |
| Worker / telefoto | `PXL_20261011_142800711.jpg` | 2448×3264 |
| Worker / frontal | `PXL_20261011_142820648.MV.jpg` | 1744×2320 |
| Fuentes / principal | `PXL_20261011_142434937.jpg` | 3000×4000 |
| Fuentes recompilado / principal | `PXL_20261011_143425648.jpg` | 3000×4000 |
| Original restaurado / principal | `PXL_20261011_143043035.jpg` | 3000×4000 |

En worker, pulsar a los 3 s de la apertura produjo un JPEG final observado a
los 7,578 s. En fuentes, la pulsación a los 3 s no produjo JPEG en el intervalo
de 20 s; esperar 6 s sí produjo JPEG, observado a los 10,428 s. Son verificaciones
funcionales individuales: la primera prueba de fuentes a 3 s pertenece al
bloque de compilación no confirmada y no demuestra una regresión del parche.
Tras recompilar correctamente fuentes, pulsar a los 3 s sí produjo JPEG,
observado a los 9,279 s. El original restaurado también capturó con pulsación
a los 3 s, observado a los 8,249 s. Cada caso tiene una sola repetición.
Incluyen procesamiento y polling, el input puede
encolarse y no demuestran mejora de latencia o calidad fotográfica. No se
hicieron nuevas pruebas DNG, SINGLE/TORCH, todos los modos ni análisis objetivo
de calidad. No se modificó el pipeline fotográfico.

## Artefactos y reproducción

Todo queda en `gcam/apk-analysis/`, separado del módulo RAW:

- `StartupWorker.smali`: helper del worker.
- `prepare_thread_trial.py`: valida las 46 clases e inserta el hook.
- `prepare_font_trial.py`: extiende el worker con las tres fuentes.
- `AssembleSmali.java`: ensambla un directorio DEX con apktool instalado/API 28.
- `repack_dex_trial.py`: guarda hash original, valida cabecera/checksums/referencias
  DEX y verifica que sólo cambia el contenido de `classes2.dex` en el ZIP.
- `summarize_threads.py`: conserva corridas, exclusiones y estadísticas.
- `mount_trial.py` y `capture_probe.py`: herramientas de ensayo ya existentes.

Los APK, smali extraídos, logs, fotos y respaldo privado están bajo
`dist/analysis/gcam-threading-20261011/` (ignorado por Git). No se distribuye una
refirma ni una actualización instalable: la reconstrucción invalida la firma
original. Las variantes se ejecutaron mediante montaje root temporal del APK
del paquete existente, con hashes comprobados y sin desactivar verificaciones
de firma. No se combinaron con scan6 ni con el parche de logging anterior.

| Artefacto | SHA-256 |
|---|---|
| Original | `132e18273b3aafdb93e851f5db88156bd4f82c5032ad8de6594fa5a49ea6fe89` |
| control39.apk | `63751e39638ce8956312da0e2dc28ed6e8b5625ff07510442f87e0b1d06ad2d0` |
| worker39.apk | `18f4a643e791d80909e583730a9306a58054edb7df6bb2021540ead606dc0928` |
| fonts39.apk | `7277601f0d17b10758c6146d642dd6c700cbbd175d41bface4a60e7921bf935d` |
| app-backup.tar, host y dispositivo | `3e44257340be31e3ac94a0984c0d268c3fd1c64c2ee5dd52b61bdba7872f821e` |

Para reproducir una construcción, crear una copia nueva del directorio
`apktool/smali_classes2` en un directorio de ensayo y conservar aparte un control
sin cambios. Aplicar `prepare_thread_trial.py DIRECTORIO --original-smali RUTA_APKTOOL`.
Sólo para fuentes, ejecutar después `prepare_font_trial.py DIRECTORIO`.
Ensamblar con:

```powershell
java -Xmx3072m -cp C:/Windows/apktool.jar gcam/apk-analysis/AssembleSmali.java DIRECTORIO/smali_classes2 SALIDA.dex
python gcam/apk-analysis/repack_dex_trial.py dist/analysis/startup-20261011/gcam-current.apk SALIDA.dex SALIDA.apk --label nombre
```

Los scripts de preparación están limitados a esta versión extraída. Ensamblar
cada variante antes de cambiar la copia de smali. No sobrescribir artefactos ya
medidos. Aplicar/restaurar con `mount_trial.py` y el hash exacto correspondiente;
esperar el fin de cada colector y comprobar `Success` de ART antes del siguiente.
Resumen reproducible:

```powershell
python gcam/apk-analysis/summarize_threads.py dist/analysis/gcam-threading-20261011/measurements
```

## Estado final y siguiente cambio razonable

APK original verificado y montaje vacío; ART `speed-profile` recompilado con
`Success`. Metastore y pipelinepolicy conservaron sus hashes previos. No se creó
un módulo APatch/Magisk ni se alteró el módulo RAW. Se conservaron configuraciones
y fotos; los cuatro APK temporales del dispositivo se retiraron después de
restaurar. La compilación sintáctica Python y la comprobación de higiene del
repositorio finalizaron correctamente; ésta validó también los dos módulos RAW.

La separación aplicada sirve como experimento pequeño, no como solución general.
Para reducir cientos de milisegundos de UI, el siguiente cambio debería medir
y aplazar un inicializador secundario concreto de opciones/interfaz hasta después
de la primera preview, manteniendo su trabajo de vistas en el hilo principal.
Para trabajo pesado de CPU/I/O se necesita aislar una función sin dependencia
de View o estado de Activity y publicar sólo su resultado. No hay evidencia
suficiente para cambiar de executor toda la inicialización de `jpp`/`jnr`.
