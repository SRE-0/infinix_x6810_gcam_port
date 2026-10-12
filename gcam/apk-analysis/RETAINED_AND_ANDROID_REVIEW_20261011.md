# APK conservado y revisión del arranque — 2026-10-11

**Actualización posterior:** este informe describe la base 0.1.0. Se desarrolló,
midió y conservó la carga diferida de filas en el módulo 0.2.0; ver
[resultados e instalación vigente](LAZY_OPTIONS_RESULTS_20261011.md).

La variante `profile-cache-scan6-release.apk` queda activa por petición del usuario.
Combina caché limitada a una construcción de perfiles de vídeo y barrido de IDs
0–5, comprobados en este X6810. Las mediciones intercaladas anteriores dieron
una mediana del frame de actividad con preview de 3214 a 2614 ms y controles
de captura de 3066 a 2428 ms. Son indicadores instrumentados, no una medición
óptica de latencia ni TTFD. Véanse [método y límites](PROFILE_RESULTS_20261011.md).

## Instalación conservada

Se instaló y activó el módulo independiente `x6810_gcam_startup` 0.1.0 mediante
APatch. No se modificaron los módulos RAW, los datos de GCam ni el APK original
subyacente. El SHA-256 del APK activo es
`83d8f56956bd6ad35430636591b672090f065486fcc6f76e1e964a6c05ca763b`.

Se verificaron activación, restauración al hash original y nueva activación
mediante `service.sh`. APatch conserva la instalación en `modules_update` hasta
el siguiente reinicio. El servicio para ese arranque está configurado; **no se
ha verificado todavía un reinicio real**. [Código e instrucciones](../apatch-startup/README.md).

## Traza del APK optimizado

Artefactos locales privados: `dist/analysis/gcam-retained-20261011/`.
La traza `optimized_trace_01` no perdió eventos por sobrescritura del buffer,
pero Perfetto informó 220 errores de interpretación y faltan nombres de
procesos. No se atribuyen todos los hilos concurrentes a GCam.

| Sección | Tiempo transcurrido | CPU del hilo principal | Interpretación |
|---|---:|---:|---|
| `makeApplication` | 359 ms | 302 ms | Inicialización aún costosa |
| `cameraUiModule` inflate | 350 ms | 319 ms | Predomina construcción de UI |
| Controller initialize | 1154 ms | 773 ms | Incluye secciones siguientes; no sumar |
| `UiWirer#wire` | 448 ms | 352 ms | Construcción y conexión de vistas |
| `updateOptionsBar` | 342 ms | 206 ms | Otros 133 ms esperando CPU, 3 ms en D |
| PHOTO module controller | 135 ms | 46 ms | 57 ms durmiendo; requiere analizar dependencia |

El primer frame recibido del sensor aparece antes de terminar el controlador.
Por tanto recibir imágenes no equivale a tener preview y disparador utilizables.
Estos valores son de una traza diagnóstica, no un nuevo ensayo A/B.

## Dependencias encontradas en código

`nsu.a` comprueba el hilo principal e infla inmediatamente los `ViewStub` del
panel de opciones. Aunque el contenido empieza oculto, se construyen sus vistas,
coordinador, comportamiento del panel y listeners. Los consumidores posteriores
usan los campos inicializados: aplazar el método completo exige adaptar esos usos.

`kzh.run`, caso 9, ejecuta `updateOptionsBar`: limpia contenedores y reconstruye
filas. `jyh`, caso 17, crea `lfu` y sus widgets por opción; `leb.o` y
`OptionsMenuView.B` recorren colecciones de filas. Es candidato a reutilización
e indexación, pero la traza no demuestra actualizaciones duplicadas que puedan
eliminarse sin cambiar comportamiento.

`pdh.c(Runnable)` ejecuta directamente si ya está en el hilo UI. Su otro camino
y `pdh.execute` usan un Handler del Looper principal. Usar estos ejecutores no
convierte el trabajo en tarea de fondo.

JADX produjo errores en partes del APK; la revisión cubre las rutas críticas
y sus dependencias, no una validación exhaustiva de cada clase y modo.

## Aplicación de la documentación oficial

Android recomienda aplazar operaciones no esenciales y medir de nuevo; los
workers también compiten por CPU. Esto encaja con la espera observada en la
barra de opciones. [Análisis y optimización del arranque](https://developer.android.com/topic/performance/appstartup/analysis-optimization).

| Prioridad | Cambio candidato | Condición de implementación |
|---|---|---|
| 1 | Crear filas del panel oculto al abrirlo | Mantener disponibles estado y callbacks; comprobar apertura temprana del panel |
| 2 | Reutilizar filas e indexarlas por opción | Invalidar al cambiar modo, cámara, tema e idioma |
| 3 | Preparar datos independientes de UI en un worker | Aplicar vistas en main, controlar ciclo de vida y cancelación |
| 4 | Regenerar perfiles ART para los DEX exactos | Comparar compilación y arranque sin confundir perfil incluido con perfil aprendido |

La carga bajo demanda mediante `ViewStub` está documentada, pero no admite
layouts raíz `<merge>`: `options_menu_layout` usa precisamente esa raíz y no
puede convertirse directamente en otro stub. [Carga de vistas bajo demanda](https://developer.android.com/develop/ui/views/layout/improving-layouts/loading-ondemand).

Las vistas deben permanecer en el hilo UI. Mover todo el controlador o los
constructores de widgets a workers no es una solución válida.
[Hilos y rendimiento](https://developer.android.com/topic/performance/threads).
`AsyncLayoutInflater` requiere constructores y parámetros de layout compatibles
con ejecución de fondo; no basta introducirlo en un árbol arbitrario con vistas
personalizadas. [Restricciones de AsyncLayoutInflater](https://developer.android.com/reference/androidx/asynclayoutinflater/view/AsyncLayoutInflater).

## Perfil de compilación incluido: hallazgo independiente

`assets/dexopt/baseline.prof` del original contiene entradas para tres DEX.
Sus checksums no coinciden con los CRC32 de los DEX del APK original; los
recuentos de métodos de los primeros dos tampoco coinciden.

| DEX | Checksum del perfil incluido | CRC32 del ZIP original | Métodos perfil / DEX |
|---|---|---|---:|
| classes.dex | e107e005 | 2b3f4700 | 65532 / 65457 |
| classes2.dex | 78cb1dfc | 2b7d9e66 | 42542 / 64061 |
| classes3.dex | d741a747 | c8ab96cd | 5563 / 5563 |

Para DEX dentro de APK, ART usa CRC32 de la entrada ZIP como checksum de
ubicación. [Código oficial de ART](https://android.googlesource.com/platform/art/+/master/libdexfile/dex/dex_file.h).
El analizador reproducible es `inspect_baseline_profile.py`.

Esto apunta a un perfil incluido de otra compilación, pero **no implica ausencia
de optimización ART**: `profman` confirmó que los perfiles `cur` y `ref` del
teléfono sí contienen los checksums y recuentos del APK modificado activo.
No hay evidencia nueva de mejora por regenerar el perfil. Cambiar únicamente
los checksums sería incorrecto si cambiaron los índices de métodos.

Baseline Profiles permiten compilación anticipada; Startup Profiles intervienen
en la organización del DEX durante la compilación con D8/R8. No son la misma
función ni una opción equivalente del teléfono.
[Diferencias oficiales](https://developer.android.com/topic/performance/baselineprofiles/difference-baseline-startup).

No se integró todavía un parche adicional de UI: las mejoras conservadas son
las ya medidas de caché y scan6. No se acredita mejora de calidad fotográfica
ni de enfoque del telefoto; la comprobación anterior cubrió JPEG de las tres
cámaras y transición PHOTO/vídeo, con los límites descritos en su informe.
