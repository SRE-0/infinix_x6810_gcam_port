# Panel de opciones: módulo 0.5.0

La optimización nueva difiere las suscripciones de valores visibles y la
preparación de las pestañas del panel PHOTO hasta su primera apertura. Conserva
las filas diferidas de 0.2.0, el CRC corregido de 0.3.0 y la caché nativa de 0.4.0.
No cambia parámetros fotográficos, modelos, delegados, codecs ni el HAL.

## Qué se difiere y qué sigue al inicio

`nsu.a()` mantiene la inflación de la estructura del panel, `leb.k`, el
coordinador, BottomSheetBehavior, gestos, ciclo de vida, cámara y minibar. Esos
campos tienen consumidores antes de abrir el panel. Saltar la estructura completa
dejaría referencias necesarias sin inicializar.

El recorrido con `jyh` caso 13 conecta observadores cuyo callback `kgd` caso 7
actualiza exclusivamente `OptionsMenuView.A(category, value)`. En PHOTO cerrado
se guarda ese recorrido en la instancia de `leb`; la primera apertura lo ejecuta
y lee el valor actual, sin guardar una copia anticuada de la preferencia.
Los `piw` siguen registrados en el `pdf` original del ciclo de vida.

El recorrido caso 14 sigue al inicio: llama a `ler.m(leb)` y varios consumidores
actualizan disponibilidad, minibar y estado de cámara. No se confunde con el
recorrido puramente visual. La aplicación sigue recibiendo esos cambios aunque
el panel permanezca cerrado.

La preparación de TabLayout/ViewPager, adaptador, listeners, dos tabs y márgenes
se extrae del CFG original a `PanelTabs.build`. Conserva sus 534 líneas de
instrucciones/etiquetas y sus constantes de entrada; no cambia sus instrucciones.
Se ejecuta una vez por instancia antes de mostrar el panel. No se mueve ninguna
operación de vista a un worker.

La primera apertura pasa por el helper ya existente `x6810OpenOptions`: prepara
suscripciones y tabs antes de refrescar filas. También lo usa el callback de
expansión del BottomSheet. Fuera de PHOTO cerrado se conserva preparación eager.
La instancia libera las referencias pendientes al conectar los observadores;
no hay cola global ni callback retardado que capture una Activity antigua.

Solo cambian `nsu`, `leb` y la clase añadida `x6810/gcam/PanelTabs` respecto a
los fuentes secundarios retenidos. El DEX principal mantiene el CRC y scan6.
Los payloads se verifican por hash y solo cambian classes.dex/classes2.dex
respecto al APK original; la modificación nativa sigue siendo la de 0.4.0.

## Comparación A/B/B/A

Mismo DEX principal con CRC corregido, biblioteca nativa corregida, logging BSG
desactivado y ART `speed` en ambas variantes. Cuatro bloques con un calentamiento
excluido y tres aperturas medidas cada uno: seis por variante. Force-stop entre
aperturas, filesystem caliente; sin capturas de pantalla durante el benchmark.
No se controlaron DVFS/temperatura ni procesos externos.

| Métrica, mediana | Control 0.4.0 | Panel diferido | Diferencia |
|---|---:|---:|---:|
| Enlace de UI | 387,636 ms | 337,685 ms | −49,951 ms (12,9 %) |
| Inicialización del controlador | 698,924 ms | 647,476 ms | −51,448 ms |
| Primera pantalla TTID | 1446,5 ms | 1426 ms | −20,5 ms |
| Preview renderizada, desde marcador ADB | 2468,655 ms | 2434,549 ms | −34,106 ms |
| Disparador habilitado, desde marcador ADB | 2407,417 ms | 2312,845 ms | −94,572 ms |
| Preview y disparador disponibles conjuntamente | 2468,655 ms | 2449,454 ms | −19,201 ms |

El enlace de UI tiene rangos separados: control 366–394 ms, variante 324–351 ms.
El promedio de disponibilidad conjunta pasó de 2530,111 a 2441,178 ms
(−88,933 ms; 3,5 %); las medianas muestran una mejora menor. El promedio TTID
de la variante fue 1420 ms. Su disponibilidad conjunta varió de 2394 a 2476 ms.
Se conservan las doce muestras, incluida la apertura control más lenta.
No se acredita significancia estadística ni un ahorro universal de 89 ms.

Las marcas combinan timestamps del log con el reloj de eventos internos,
incluyen overhead ADB y no son una medición óptica desde el toque. No sumar
estos ahorros a medianas de ensayos anteriores. Ninguna apertura medida registró
FATAL EXCEPTION, Fatal signal ni ANR.

## Comprobación del panel

La sonda temporal registra preparación diferida de valores/tabs en menos de
0,2 ms al iniciar. En la primera apertura principal, la preparación del tab
tardó 41,444 ms y el helper completo 42,577 ms; al reabrir no creó tabs otra vez.
Es tiempo de CPU/eventos Java, no latencia óptica de apertura completa del panel.
La primera apertura paga el trabajo aplazado, además de las filas ya diferidas.

La versión de distribución sin sondas pasó:

- Primera apertura por toque y por gesto tras detener el proceso.
- General y Pro, con control RAW presente; igualdad de textos, descripciones y
  selección de la jerarquía del panel frente al control.
- Google AWB off → on → off, con selección y etiqueta actualizadas.
- Reapertura del mismo panel, cambio frontal/principal/telefoto y regreso a 1.0.
- PHOTO → Retrato → PHOTO y recuperación tras HOME/reanudación.

La primera sonda se detuvo por esperar enfoque en la frontal. Se verificó luego
que el control tampoco lo ofrece; no era un fallo del parche. La repetición
`functional-release` corrigió esa expectativa y completó todas las comprobaciones.
No se ejecutó una acción de accesibilidad específica: se conserva su callback
de expansión y se verificó la ruta por gesto, sin afirmar equivalencia de pruebas.

## ML y microvideo: resultado de la revisión

El escalonamiento adicional no está integrado. La sonda identifica ahora las
fábricas efectivas, en lugar de atribuir los codecs de PHOTO al encoder Imax
`jbe.f()` solo por aparecer en el APK. En dos aperturas diagnósticas principales:

| Evento, desde onCreate | Apertura 1 | Apertura 2 |
|---|---:|---:|
| Preview y disparador ya disponibles | 1821,79 ms | 1919,93 ms |
| Primer factory de imagen `kob` | 1713,96 ms | 1865,41 ms |
| Primer factory de encoder `qiv` | 2025,17 ms | 2427,07 ms |
| Entrada JNI al segmentador de retrato | 2414,90 ms | 2307,42 ms |

Los dos factories `qiv` de cada apertura y el segmentador comenzaron después
del arranque útil en estas muestras. No se demuestra que posponerlos más reduzca
la apertura. `kob` es una ruta de encoder de imagen distinta, no el factory de
microvideo, y empieza antes de la preview final; no se ha eliminado su trabajo.

`kch.b()` publica incondicionalmente el texto `Attempting to init encoder that
is shut down!` antes de comprobar `e`, incluso en inicialización normal. El smali
confirma que ese mensaje por sí solo no prueba que `f` esté cerrado ni una
carrera. Se mantiene el log original; no se presenta su ausencia como mejora.
`kdg` caso 9 es una precarga de microvideo; el inicio y uso efectivos mantienen
handlers, futures y consumidores originales. El manager del segmentador también
mantiene su bloqueo, comprobación de handle, carga/decrypt/checksum y fallback.

Otros modelos CPU/GPU aparecen antes o después de esos eventos. Esta sonda no
audita todas sus dependencias ni prueba un planificador general de ML. Por eso
no se declara completado un nuevo escalonamiento de todos los modelos, ni se
añaden sleeps, serializaciones globales o hilos arbitrarios. El punto pendiente
de la lista es un escalonamiento adicional que demuestre beneficio y conserve
Top Shot/Motion Photo, audio, captura inmediata y cambios de modo.

Android recomienda comprobar la necesidad de cada operación y volver a medir
antes de cambiar la ruta de inicio:
[análisis y optimización](https://developer.android.com/topic/performance/appstartup/analysis-optimization).
Las vistas conservan el hilo principal según
[hilos de Android](https://developer.android.com/topic/performance/threads).

## Artefactos y reproducción

La evidencia privada (doce aperturas ABBA, JSON, sondas DEX, jerarquías, logs y
capturas) se guardó bajo `dist/analysis/gcam-panel-20261011/` y se eliminó
durante la limpieza local de octubre de 2026. Este informe conserva los
resultados resumidos; reproducirlos requiere volver a preparar las entradas y
capturar datos en el dispositivo.

| Payload | SHA-256 |
|---|---|
| APK distribución | `2218c653d91482b377877014bbc22610cb386c30465c4b831c944299f0ea1b83` |
| Native, idéntico a 0.4.0 | `64cfcb3f598cdf3e75875bdd4cb8e8775a6763be15c3d2240d1d7ee0656f053a` |
| ZIP APatch 0.5.0 | `973bdc375f1d1c4d78b9a9cfbe7bfcb35300a54e68a5c24a45d2ed08286e239f` |

`prepare_panel_trial.py` prepara el cambio sobre el secundario de lazy-options.
`AssembleSmali.java` ensambla DEX 039. `repack_dex_trial.py` usa el DEX principal
CRC conservado; `prepare_lazy_options_release.py` retira las marcas de timing.
`benchmark_panel.py` conserva la biblioteca corregida en ambos lados y restaura
ambos montajes en finally. `verify_panel_candidate.py` usa jerarquías frescas y
restaura el módulo activo al terminar.

```powershell
python gcam/apatch-startup/build.py gcam/apatch-startup/payload/x6810-gcam-startup-0.5.0.apk dist/x6810-gcam-startup-0.5.0.zip --native gcam/apatch-startup/payload/libgcastartup-cache.so
```

## Instalación y capturas finales

El ZIP 0.5.0 se instaló con APatch y se activó sin reiniciar. `activate.sh status`
confirmó los dos montajes propiedad del módulo y los hashes anteriores. La
promoción de `modules_update` mediante un futuro reinicio no se verificó.

La comprobación final conservó preview y disparador visibles y produjo JPEG
decodificables en los tres sensores: principal 3000×4000, frontal 1744×2320 y
telefoto 2448×3264. La última captura tiene sufijo `.MV.jpg`; esto no acredita
por sí solo reproducción ni sincronización de audio del microvideo incrustado.
Los hashes, tamaños y nombres están en `final/captures-summary.json` de la
evidencia privada. Se dejó PHOTO y cámara principal 1.0 seleccionados.

No aparecieron FATAL EXCEPTION, Fatal signal, ANR ni el error de apertura de
caché en los logs finales. La apertura final aislada tuvo TTID 2044 ms; no
reemplaza el promedio del benchmark ni mide disponibilidad completa. Las
capturas verifican funcionamiento, no una mejora de calidad fotográfica. No
se repitió toda la batería RAW, OIS y flash, cuyos componentes no cambiaron.
