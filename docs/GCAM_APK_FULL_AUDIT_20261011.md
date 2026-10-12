# Auditoría de apertura del APK BSG 9.7 — 2026-10-11

**Módulo vigente: 0.5.0**, con [panel diferido y revisión de ML/microvideo](GCAM_PANEL_OPTIMIZATION_20261011.md).
Conserva los parches CRC y caché nativa. Este documento es la auditoría histórica.

**Versión anterior: 0.4.0**, con [caché del segmentador corregida](GCAM_SEGMENTER_CACHE_FIX_20261011.md)
en la biblioteca efectiva en ejecución. Conserva el APK de 0.3.0.

**Actualización posterior:** el primer defecto se corrigió e instaló como
0.3.0. Ver [implementación, recuperación y comparación A/B](GCAM_CRC_FIX_20261011.md).
Este documento conserva los hallazgos del APK 0.2.0 auditado.

Se extrajo nuevamente el APK activo del teléfono, se decodificaron sus tres
DEX, Manifest y recursos y se inventariaron sus bibliotecas ELF. La revisión
semántica se concentró en las rutas de arranque y sus dependencias. El hallazgo
prioritario es una biblioteca nativa oculta que se vuelve a extraer por una
comparación CRC incompatible con la transformación de su cabecera.

## Alcance y reproducibilidad

- APK activo: SHA-256 `628012f407d7df89b6d7064cc5be6e103d4a0652de7123ddddd4a2295b17759d`.
- Estado: APatch `x6810_gcam_startup` 0.2.0, caché de perfiles, scan6,
  filas de opciones diferidas y ART `speed`. No se modificó el APK en esta auditoría.
- El APK privado, los índices, las trazas y el árbol apktool se guardaron
  originalmente bajo `dist/analysis/`; se eliminaron durante la limpieza local
  de octubre de 2026. Este informe conserva los hallazgos y métricas resumidos.
  Repetir la auditoría requiere proporcionar de nuevo el APK compatible.
- JADX 1.5.6 terminó con 2220 errores. Su Java es una ayuda de lectura,
  no fuente reconstruida compilable. Se contrastaron los puntos críticos con smali.
- `index/calls.sqlite`: 17188 clases, 107683 métodos definidos,
  457957 instrucciones invoke y 401925 referencias a campos.
- `index/audit.json`: cabeceras DEX, 63 componentes Android, siete providers,
  21 bibliotecas nativas del directorio `lib/`, dependencias ELF e imports.
- `hardware/`: propiedades, configuración de codecs, mapas de memoria e hilos.
- `full_audit_trace/`: traza, análisis de intervalos y estados del hilo principal.
- `full_audit_extended/`: apertura con registro extendido de 15 segundos.

El índice es sintáctico: no resuelve todos los destinos de interfaces,
reflexión o JNI. Los ELF se inventariaron y se relacionaron con las rutas Java;
no se reconstruyó el código fuente completo de todos sus algoritmos. Hay además
código nativo dentro de assets, descrito a continuación. No equivale a una
auditoría funcional exhaustiva de cada método y cada modalidad fotográfica.

## Defecto comprobado: extracción repetida de 39 MB

`com.android.app.Application.b()` abre el APK como ZIP y extrae
`assets/QrQJbYT787QDr7Co` a
`/data/user/0/com.android.MGC_9_7_047/cache/codec_hevc.lck`.
Antes de escribir cambia los tres primeros bytes de `00 00 00` a `7f 45 4c`,
reconstruyendo la cabecera ELF. Después carga ese archivo con `System.load`.
El nombre no demuestra que sea un codec HEVC de Android.

Para decidir si puede reutilizarlo, compara `bc(File)` con `ZipEntry.getCrc()`.
El smali de `bc` confirma un CRC32 del contenido real, leído en bloques de 8192
bytes. Se extrajo una copia íntegra por ADB pull para comprobarlo:

| Representación | Tamaño | CRC32 |
|---|---:|---|
| Asset original, cabecera enmascarada | 38953640 bytes | `a6628e96` |
| Archivo nativo extraído, cabecera ELF | 38953640 bytes | `4502f6fb` |

Todos los bytes desde el cuarto coinciden. El CRC del asset con la cabecera
restaurada también es `4502f6fb`. La condición actual siempre considera inválida
esa copia. La fecha de modificación pasó de `19:55:17.872` a `19:59:01.724`
tras otra apertura en frío; el tamaño y contenido permanecieron iguales.
La apertura de comprobación dio TTID 2033 ms, sin variante corregida para comparar.

**Corrección propuesta:** conservar la validación, pero calcular para esta ruta
el CRC de la representación original, normalizando a cero solamente los tres
bytes conocidos y verificando primero la cabecera ELF y el tamaño. Alternativa:
validar contra una huella explícita de la representación transformada, ligada
al asset de esta versión. No basta con comprobar `exists()` ni fijar un CRC
global para otros archivos. La primera instalación, actualización del APK y
copia corrupta deben seguir provocando extracción. Una escritura mediante
archivo temporal y reemplazo evita dejar una copia incompleta.

Esto elimina la extracción repetida, pero aún leería 39 MB para validar CRC.
Una segunda fase podría usar una marca de versión e integridad almacenada de
forma coherente, evaluando sus garantías. No trasladar `System.load` a un worker
sin resolver las dependencias de JNI y del patcher. Todavía no se ha medido
el ahorro de una corrección; este documento no atribuye a ella toda la demora.

## Dónde se consume el hilo principal

Una nueva traza en el estado activo dio TTID 1836 ms; otra apertura extendida,
2103 ms. Son observaciones de diagnóstico, no una comparación A/B. TTID mide
la primera visualización de la actividad, no la disponibilidad del disparador.

| Intervalo del hilo principal | Tiempo transcurrido | CPU ejecutando |
|---|---:|---:|
| bindApplication | 851.7 ms | 655.2 ms |
| makeApplication | 527.8 ms | 454.8 ms |
| CameraActivity onCreate | 465.2 ms | 432.3 ms |
| cameraUiModule inflate | 423.0 ms | 397.3 ms |
| ControllerInitializer initialize | 955.3 ms | 718.4 ms |
| UiWirer wire | 515.6 ms | 437.4 ms |
| OptionsBarCtrl wireAutobahn | 175.7 ms | 151.4 ms |
| getModuleController:1 | 136.2 ms | 59.0 ms |
| GCA App component | 84.3 ms | — |

Los intervalos están anidados y **no se suman**. En ControllerInitializer hay
140.3 ms runnable: competencia por CPU también importa. La traza registra
288 errores de parsing de eventos del proveedor; los resultados describen los
eventos interpretados, no una reconstrucción perfecta del sistema.

## Mejoras por prioridad y restricciones

| Prioridad | Cambio concreto | Condición para aplicarlo |
|---|---|---|
| 1 | Corregir la validación/extracción de la biblioteca oculta | Mantener integridad y recuperación; medir extracción y tiempo de apertura por separado |
| 2 | Diferir la construcción del panel oculto de opciones | Mantener botones, estado, observadores y acceso inmediato al panel |
| 3 | Corregir la caché del motor de segmentación | Identificar contrato JNI y argumentos; verificar beneficio sin cambiar salida del modelo |
| 4 | Reducir inicializaciones ML/video competidoras durante PHOTO | Respetar contexto EGL, pre-roll y dependencias de captura |
| 5 | Desactivar logging exhaustivo en uso normal y corregir su limpieza | A/B reversible, conservar diagnóstico cuando sea necesario |
| 6 | Optimizar providers y componentes residuales | Medir cada initializer y demostrar que no lo requiere una ruta temprana |

### Panel de opciones

`nsu.a()` exige el hilo principal e infla tanto la entrada como el bottom sheet
oculto. La versión activa difiere filas, pero todavía construye y conecta la
estructura del panel. El intervalo wireAutobahn es una oportunidad de unos
176 ms observados, no un ahorro garantizado de ese tamaño.

`leb` publica campos usados por `ldw`, `ldx`, `ldy`, `ldz`, `lea`, `nsp`,
`jyh`, `kef`, `kgd`, `kzh` y ViewPager. El índice de consumidores está en
`index/leb-field-consumers.json`. Se necesita `ensurePanel()` en el hilo principal,
estado pendiente y protección frente a cierre/cambio de modo. No omitir
simplemente `nsu.a()`: las llamadas llegan también por la interfaz `ntg.a()`.
No inflar Views ni manipular Choreographer en un executor general.

### Application e hilos

`CameraContentProvider.onCreate()` inicializa el componente antes de
`Application.onCreate()`. `CameraApp.e()` publica su campo volatile `o` antes de
terminar inyección e inicialización. Mover todo ese método a otro hilo permitiría
que consumidores observen un componente incompleto. Requiere construcción local,
publicación final y revisión de todas las dependencias; el componente medido es
menor que los costes de interfaz.

`pdh` es un executor del Looper principal, no un pool de trabajo. Sus tareas
pueden ejecutarse inmediatamente en el mismo hilo. `lgh` ya usa executor para
flags. `jmt.run()` tiene ramas distintas: una usa Choreographer y exige main.
`pkt` ya abre Camera2 mediante callbacks/Handler. Sus latches requieren revisar
cada caller; no se observó una espera de cinco segundos del main que explique
por sí sola el síntoma.

El cargador `pjc/pjb` sincroniza cargas de bibliotecas y llama al RamPatcher.
Una precarga indiscriminada puede añadir espera del mismo lock. El ensayo previo
de worker nativo no mostró mejora consistente y fue retirado.

Separar servicios mediante `android:process` añade otro arranque, IPC y estado
duplicado. No es una optimización justificada para estas rutas. Se prefieren
tareas acotadas, diferidas y con dependencias explícitas.

### GPU, ML y caché

El dispositivo identifica MT6785 y Mali-G76 MC4. `libOpenCL.so` existe y está
mapeada por GCam. Los logs muestran GPU delegate con 271/271 nodos y otros
modelos de 71/71 y 76/76; XNNPACK CPU participa en otros grafos. La GPU ya se usa.

El registro extendido reproduce:
`Unable to open file for writing: Is a directory`, seguido de
`Could not initialize inference engine`, sobre la ruta de caché externa del
paquete. Aparece varios segundos después del primer arranque de controles en
un worker. Es un fallo real; aún no se demuestra que bloquee la primera preview.

Revisar `lqv.b`, `tkn` y
`NativePortraitSegmenterInterface.initSegmenter(JJStringStringZZZZZ)` para conocer
qué parámetro espera directorio, archivo o token. No reemplazar el directorio
de caché por un archivo ni cambiar todas las cadenas similares. La serialización
del delegado OpenCL puede reducir compilaciones; requiere soporte de esta build,
token por modelo/dispositivo y medición de creación e inferencia.

Las bibliotecas vendor neuron/APU están presentes, pero eso no verifica soporte
NNAPI, operadores ni compatibilidad de los modelos. Las referencias Hexagon,
GXP y EdgeTPU en strings corresponden a otras rutas; no se activan de forma
segura fingiendo otra plataforma.

### Codecs y microvideo

Se observó selección efectiva de `OMX.MTK.VIDEO.ENCODER.AVC` y varias
inicializaciones de encoder durante el arranque. `jbe.f()` obtiene el contexto
EGL actual y texturas antes de preparar el encoder. Moverlo a un hilo arbitrario
puede invalidar ese contexto. Se requiere un HandlerThread con contexto compartido
y orden correcto de superficies y callbacks.

Diferir microvideo hasta preview estable podría reducir competencia, pero puede
perder frames previos de Top Shot/Motion Photo. Se debe medir con esas funciones
y audio. Cambiar AVC por HEVC no acelera la inflación de Views, DEX, apertura del
sensor ni procesamiento RAW; además cambia capacidades y compatibilidad.

### Logging y ART

`com.b` inicia captura `logcat *:V` y limpieza de archivos. La reconstrucción
Java muestra un bucle que avanza solo cuando delete tiene éxito; confirmar y
corregir esa rama en smali evita reintentos infinitos ante un archivo indeleble.
El logging continuo compite por I/O; probar su preferencia mediante copia y
restauración, sin retirar los logs necesarios para el experimento.

ART `speed` ya está aplicado. No reordena los DEX ni elimina trabajo de interfaz.
El primer arranque tras reiniciar sigue pendiente por la carrera con compilación
del overlay, documentada en el estado vigente. Los avisos de verificación de
locks y la ofuscación son candidatos de investigación, no permiso para eliminar
bloques opacos. Las bibliotecas `lib/` se extraen al instalar; no se descomprimen
135 MB de `libgcastartup.so` en cada apertura. La extracción repetida comprobada
afecta al asset separado de 39 MB.

## Validación de una implementación

Primero aislar la corrección CRC: mismo APK/base ART, misma configuración,
variante control y parche en secuencia alternada, al menos diez aperturas por
variante con pantalla desbloqueada. Registrar CRC, fechas de extracción, tiempo
del cargador, TTID, primera preview y disparador disponible. Comparar medianas,
dispersión y fallos; no usar exclusivamente `am start -W`.

Comprobar también cache ausente, archivo truncado/corrupto, cambio de APK y
primer arranque tras reinicio. Después probar captura/guardado de las tres cámaras,
RAW/JPEG, cambio de modos, apertura inmediata del panel, video, Motion Photo,
segmentación, flash y recuperación tras pausa. Ningún cambio de esta auditoría
demuestra una mejora de calidad fotográfica todavía.

## Documentación primaria aplicada

- [Android: análisis y optimización de arranque](https://developer.android.com/topic/performance/appstartup/analysis-optimization): diferir trabajo ajeno a la primera pantalla y medir sus dependencias.
- [Android: tiempos de lanzamiento](https://developer.android.com/topic/performance/issues/launch-time): distinguir TTID y TTFD.
- [Android: hilos](https://developer.android.com/topic/performance/threads): afinidad de UI y competencia de recursos.
- [MediaCodecInfo](https://developer.android.com/reference/android/media/MediaCodecInfo): capacidades e identificación de codecs hardware; no asumir rendimiento por nombre.
- [LiteRT: GPU nativa](https://developers.google.com/edge/litert/android/gpu_native): contexto EGL, afinidad y opciones de serialización.
- [LiteRT: delegates](https://developers.google.com/edge/litert/performance/delegates): coste de particionar grafos y trasladar datos.

Estas guías describen mecanismos aplicables. No prueban que una configuración
de otra cámara o fabricante pueda trasladarse directamente a este APK ofuscado.
