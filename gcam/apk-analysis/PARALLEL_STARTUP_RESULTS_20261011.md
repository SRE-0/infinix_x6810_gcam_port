# Revisión de paralelismo del arranque — 2026-10-11

Referencia: versión retenida 0.2.0, con caché limitada a `hir.J`, scan6,
filas PHOTO diferidas y ART `speed`. No se modifica el módulo RAW.

## Traza nueva y límites de los hilos

Traza ADB/atrace del proceso 10366, guardada en
`dist/analysis/gcam-parallel-20261011/retained_020_trace/`.
El buffer contiene 930480 eventos, sin sobrescritura. Perfetto informa 259
`systrace_parse_failure`: el análisis de estados cubre los eventos importados
y no demuestra cobertura completa de todas las tareas. Es una ejecución con
instrumentación de trazado: sus duraciones no sustituyen las medianas del
ensayo A/B. Las ventanas están anidadas y **no deben sumarse**.

| Ventana | Duración ms | CPU principal ms | Runnable ms |
| --- | ---: | ---: | ---: |
| bindApplication | 691.744 | 531.245 | 40.954 |
| cameraUiModule#inflate | 459.543 | 382.017 | 66.643 |
| Inicializador del controlador | 825.964 | 532.284 | 212.494 |
| UiWirer#wire | 410.688 | 320.605 | 78.284 |
| OptionsBarCtrl#wireAutobahn | 145.635 | 112.443 | 28.603 |
| getModuleController PHOTO | 117.072 | 41.051 | 23.615 |

No aparece el costoso `updateOptionsBar` en este arranque: la optimización
retenida sigue actuando. Runnable significa que el hilo está listo pero espera
CPU, no que esté ejecutando código. No permite atribuir la competencia a una
aplicación concreta.

La construcción del componente y su inyección tardan 41.115 y 53.088 ms,
respectivamente. Publicar el componente desde otro hilo no basta para asegurar
que sus dependencias y efectos de inicialización sean seguros: `CameraApp.e()`
publica la referencia antes de completar toda la inyección. `pdh.a()` impone
afinidad con el hilo principal en rutas del componente y `jmt.run()`.

`lgh.run()` ya delega `PhenotypeHelper#retrieveFlags` a un executor.
`jmt.run()` tiene ramas diferentes: una usa executor y otra llama a
`Choreographer.getInstance()` y registra callbacks. No se puede mover la clase
entera sin distinguir la instancia y sus dependencias. La apertura de cámara
en `pkt` ya tiene handler/callbacks y coordinación; dividirla de nuevo requiere
demostrar un bloqueo concreto, no asumir que toda la apertura sucede en main.

## Documentación oficial aplicada

Android exige mantener la creación y manipulación de las vistas en main y
recomienda limitar los workers según la carga y ajustar sus prioridades.
Esto desaconseja repartir indiscriminadamente `inflate` y `wire` entre hilos.
[Android Developers: threading](https://developer.android.com/topic/performance/threads).

El análisis de arranque recomienda diferir trabajo no esencial y medir el
camino crítico; trasladarlo a segundo plano todavía puede competir por CPU.
TTID no acredita que la preview o el disparador estén listos.
[Android Developers: startup](https://developer.android.com/topic/performance/appstartup/analysis-optimization).

La inflación asíncrona tiene condiciones sobre constructores, Looper y
generación de LayoutParams. No se ha demostrado que la jerarquía personalizada
de GCam satisfaga esas condiciones; no se aplica como reemplazo general.
[AsyncLayoutInflater](https://developer.android.com/reference/androidx/asynclayoutinflater/view/AsyncLayoutInflater).

El JNI público de AOSP protege la primera inicialización de MediaProfiles
con un mutex. Adelantarla puede ocultar el coste, pero una llamada simultánea
puede esperar la misma inicialización. Esto es evidencia del código público,
no prueba de que las bibliotecas vendor del teléfono sean idénticas.
[AOSP MediaProfiles JNI](https://android.googlesource.com/platform/frameworks/base/+/refs/heads/main/media/jni/android_media_MediaProfiles.cpp).

## Experimento acotado

`NativeProfileWarm.smali` inicia un único worker con prioridad background en
`CameraApp.onCreate`. Hace solamente `CamcorderProfile.hasProfile(0, 0)` para
adelantar la inicialización del framework. No consulta preferencias BSG,
no retiene Activity/View, no comparte los mapas del controlador y no introduce
join, await ni espera nueva en main. Las excepciones del worker se registran;
las llamadas originales continúan intactas.

Se evita ejecutar `osh.aW` en segundo plano: decide perfiles mediante
preferencias, ID activo, facing y fallback personalizado. Ese resultado no es
una consulta nativa pura y podría quedar obsoleto al cambiar de lente.

El ensayo usa la versión 0.2.0 con los mismos eventos de diagnóstico como
control, no la antigua versión sin filas diferidas. Ambos APK compilan con
ART `speed`; secuencia ABBA, calentamiento excluido y cuatro arranques fríos
de proceso por variante. Sistema de archivos caliente; muestra pequeña.

APK experimental: SHA-256
`95dcd6d82c4db939a38e017481b88faa9c35e1f3d4565c0dc52c1105e36d59cc`.
Los cambios frente al original se restringen a los DEX principales; los
recursos y bibliotecas nativas conservan su contenido. Montaje temporal root,
sin reinstalación, borrado de datos ni cambio de firma del paquete.

## Resultado: experimento descartado

| Mediana | Control 0.2.0 | Worker | Diferencia worker-control |
| --- | ---: | ---: | ---: |
| TTID ms | 1193.500 | 1218.500 | +25.000 |
| Marcador ADB → preview renderizada ms | 2017.740 | 1989.270 | −28.470 |
| Marcador ADB → disparador habilitado ms | 2006.118 | 2014.856 | +8.739 |
| Inicialización del controlador ms | 566.434 | 553.120 | −13.314 |
| UI wire ms | 320.537 | 296.320 | −24.217 |
| Marcador ADB → steady ms | 2621.479 | 2722.383 | +100.905 |

Ocho ejecuciones medidas completas, sin FATAL EXCEPTION ni ANR registrado.
Rango de preview control: 1951.087–2121.756 ms; worker:
1944.953–2135.366 ms. Los rangos se solapan ampliamente. El worker registra
`elapsed_ms=0` en las cuatro ejecuciones medidas: la duración se redondea a
milisegundos y no significa coste nulo. En ese punto de inicialización la
consulta no ofrece un ahorro grande; tampoco demuestra que toda consulta
posterior o la inicialización anterior a onCreate sea gratuita.

La reducción de UI wire no se atribuye causalmente al worker: este no toca
vistas y su trabajo medido es inferior a la resolución del reloj. La diferencia
pequeña de preview, junto a TTID/disparador/steady peores, no acredita una
mejora visible estable. Se descarta el experimento y se conserva 0.2.0.

Datos íntegros: `dist/analysis/gcam-parallel-20261011/native-results.json`,
`native-summary.json`, y `measurements/`; no se excluyó ningún arranque medido.
El runner restaura el montaje experimental y vuelve a aplicar el módulo
retenido en su bloque `finally`. Las variantes temporales no se integran en
su payload ni en el módulo RAW.

Verificación final: montaje propiedad del módulo y SHA-256 retenido
`628012f407d7df89b6d7064cc5be6e103d4a0652de7123ddddd4a2295b17759d`,
ART `arm64 status=speed reason=cmdline`. Captura tras arranque frío con input
solicitado a 2.3 s, enviado entre 2.301 y 2.480 s; JPEG nuevo observado a
7.133 s y extraído al host. Este tiempo incluye procesamiento y no es TTFD.
El primer intento de la comprobación rechazó continuar porque la aplicación
estaba detenida y no había disparador en la jerarquía; se lanzó mediante
`CameraLauncher` y se repitió con una jerarquía fresca. El lanzamiento directo
a la actividad interna fue rechazado por Android por no ser exportada.
Comprobación de higiene del repositorio y ambos módulos: PASS;
`py_compile` de los dos scripts modificados: PASS.

## Conclusión de factibilidad

Es viable adelantar trabajo puro y acotado sin usar vistas ni estado mutable
de BSG, pero **este candidato no mejora consistentemente la apertura**. No
hay evidencia para repartir todo el controlador entre hilos. La siguiente
ruta con mayor coste observado es diferir la construcción del panel oculto
en `nsu.a()` —actualmente aún infla el contenedor, cablea callbacks y tabs—
manteniendo esas operaciones en main al primer uso. Eso requiere revisar sus
referencias anticipadas y las rutas de gesto, accesibilidad y cambio de modo;
es una propuesta posterior, no una optimización aplicada en este ensayo.
