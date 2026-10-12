# Análisis del APK instalado — 2026-10-11

**Optimización de la versión 0.5.0, conservada por el módulo 0.6.0:** [creación y suscripciones del panel diferidas](../../docs/GCAM_PANEL_OPTIMIZATION_20261011.md).
Enlace de UI: mediana 388 → 338 ms. Conserva CRC y caché nativa corregidos;
instalado sin reinicio y verificado en los tres sensores. El informe distingue
el trabajo aplicado del escalonamiento adicional de ML/microvideo pendiente.

**Versión anterior 0.4.0:** [caché del segmentador corregida](../../docs/GCAM_SEGMENTER_CACHE_FIX_20261011.md),
con biblioteca montada por separado y APK 0.3.0 conservado. La inicialización
GPU baja de 4109 a 776 ms cuando existe caché válida. Recuperación, ABBA,
restauración del módulo y capturas verificadas sin reiniciar.

**Versión anterior 0.3.0**, con [CRC del ELF corregido](../../docs/GCAM_CRC_FIX_20261011.md).
Conserva 0.2.0; evita reextraer 39 MB y mantiene detección y recuperación de
archivo ausente o dañado. Instalación y activación directa sin reinicio.
Los apartados siguientes documentan las versiones anteriores.

Nueva [auditoría del APK activo](../../docs/GCAM_APK_FULL_AUDIT_20261011.md):
inventario de los tres DEX, componentes, ELF y evidencia de extracción repetida
de una biblioteca oculta. `audit_full.py` genera el índice SQLite completo de
invocaciones/campos y `collect_hardware.py` recoge evidencia ADB de solo lectura.

**Estado vigente:** caché de perfiles + scan6 + filas de opciones diferidas,
con compilación ART `speed`, integradas en el módulo APatch independiente
`x6810_gcam_startup` 0.2.0. Ver [mediciones y verificaciones](LAZY_OPTIONS_RESULTS_20261011.md).
Nueva revisión: [factibilidad de hilos y ensayo nativo](PARALLEL_STARTUP_RESULTS_20261011.md).
El worker no mostró una mejora consistente y se conserva 0.2.0.
Los apartados siguientes conservan el análisis histórico, incluida la
[revisión de Android y traza previa](RETAINED_AND_ANDROID_REVIEW_20261011.md).

**Actualización:** se ejecutaron dos variantes mediante APatch. El barrido de
seis IDs redujo la mediana TTID 207 ms (13,4 %); el original quedó restaurado.
Ver [resultados, límites y reproducción](TRIAL_RESULTS_20261011.md).

**Prueba de hilos:** precarga de clases y fuentes en workers, control DEX
reconstruido y comprobación de las tres cámaras. Clases mostró una reducción
modesta; fuentes no mejoró de forma estable. El original quedó restaurado.
Ver [resultados del ensayo de hilos](THREAD_RESULTS_20261011.md).

El APK instalado es modificable a nivel DEX/smali y bibliotecas nativas. Se ha
completado la extracción, descompilación y revisión de las rutas principales de
arranque. Se midieron variantes modificadas mediante montajes temporales APatch;
no se firmó ni instaló una actualización permanente del paquete.

## Artefactos necesarios para repetir el análisis

El APK original extraído del teléfono, el árbol apktool, los índices y las
trazas estaban en `dist/analysis/`, excluido de Git. Se eliminaron durante la
limpieza local de octubre de 2026; este informe mantiene los hashes y hallazgos
publicables, no los artefactos privados. Para repetir el inventario, extrae de
nuevo el APK compatible mediante ADB y guárdalo en una ruta privada bajo
`dist/analysis/`:

```powershell
python gcam/apk-analysis/inventory.py dist/analysis/NUEVO/gcam-current.apk dist/analysis/NUEVO/inventory
```

El análisis histórico no es necesario para construir el módulo GCam publicado.
Su APK modificado y biblioteca nativa están versionados mediante Git LFS en
`gcam/apatch-startup/payload/`.

## Ruta de apertura y hallazgos

Las rutas siguientes son relativas a `jadx/sources/` salvo indicación contraria.

1. `com/pairip/application/Application.java`: `attachBaseContext()` crea
   `RamPatcher`, obtiene preferencias y, si `pref_disable_log_key` falta o vale
   cero, instancia `com.b`. Hay además reflexión y llamadas a
   `SignatureCheck.verifyIntegrity()`. La presencia del nombre Pairip no demuestra
   que su protección sea el cuello de botella: el verificador Java de esta
   variante devuelve verdadero en `verifySignatureMatches()`. Sigue habiendo
   código nativo/reflexivo; no se ha comprobado la aceptación de una refirma.
2. Manifest: siete proveedores, incluido AndroidX Startup con
   `androidx.work.WorkManagerInitializer`. `CameraContentProvider.onCreate()`
   llama a `initAppComponent()` y este a `CameraApp.e()`: construye el componente
   de la app antes de abrir la actividad. No se puede eliminar ese proveedor sin
   comprobar sus consumidores y la inicialización alternativa.
3. `CameraApp.onCreate()` ejecuta configuración de logging, callbacks y finalmente
   `new CameraLensesScan(); com.a.aa();` en la ruta normal. La segunda llamada
   inicializa preferencias por lente; sus escrituras usan `apply()`, no se ha
   encontrado aquí un `commit()` síncrono que explique por sí solo el retraso.
4. **`com/CameraLensesScan.java`, líneas 448–456**: `scanCameraLens()` recorre
   250 IDs numéricos y consulta `getCameraCharacteristics(String.valueOf(i))`.
   El constructor consulta antes las primeras dos cámaras de `getCameraIdList()`.
   Por tanto el escaneo amplio ocurre aunque ya exista una lista del sistema.
   Está confirmado en `apktool/smali/com/CameraLensesScan.smali`:
   método en línea 14819, consulta en 14875 y límite `0xfa` en 15171.
   No es una pausa explícita de cinco segundos: el coste acumulado de las
   consultas/excepciones debe medirse. Las cámaras auxiliares ocultas explican
   por qué un mod puede usar este barrido; sustituirlo ciegamente por la lista
   pública puede perder el telefoto.
5. **`com/b.java`, limpieza de logs**: el índice del bucle avanza únicamente
   si `File.delete()` devuelve verdadero. Si un archivo no se puede borrar, el
   mismo archivo se reintenta indefinidamente y se emite un error en cada vuelta.
   La rutina corre en un hilo separado: puede competir por CPU/I/O, pero no
   constituye por sí sola un bloqueo síncrono del hilo principal. No se observó
   evidencia de que ese caso esté ocurriendo en los logs revisados. Después
   lanza `logcat -c` y una captura continua mediante shell.
6. `CameraActivity.onCreate()` obtiene dependencias e infla `activity_main` y dos
   `ViewStub` en el hilo principal. `glc.d()` llama a `jnr.w()` dentro de
   `CameraActivityController#initialize`; `jnr.t()` construye el controlador del
   modo elegido a través de su proveedor. Mover toda esta ruta a otro hilo sería
   incorrecto: contiene vistas, estado de actividad y acceso a objetos con
   afinidad al hilo principal.

## Prioridad de modificaciones

| Prioridad | Cambio acotado | Condición antes de integrarlo |
|---|---|---|
| 1 | Sustituir el barrido 0–249 por IDs descubiertos del sistema más los auxiliares comprobados del X6810; cachear el resultado durante la vida del proceso | Medir duración y número de consultas; comprobar que principal, frontal, telefoto y modos lógicos conservan características y selección |
| 2 | Desactivar el capturador de logs mediante `pref_disable_log_key` y corregir el bucle de borrado para avanzar también cuando falla | Ensayo A/B con logging externo ADB; no confundir menor cantidad de logs con apertura más rápida |
| 3 | Aplazar inicializadores secundarios y vistas que no sean necesarias para la primera preview | Perfil por subrutina y análisis de consumidores; conservar en el hilo principal toda operación de UI |
| 4 | Revisar inicialización de WorkManager y proveedores de debug | Medir coste individual; no retirar componentes usados por trabajos, captura o servicios |
| 5 | Corregir el destino de caché TFLite únicamente si se reproduce el argumento inválido | Comparar archivo efectivo, retorno JNI y modos de retrato; el error apareció después del proxy de controles listos |

El primer parche debería limitarse al escaneo. No es suficiente cambiar el
límite `250` por `3`: los IDs pueden ser discontinuos o existir auxiliares
ocultos. La modificación necesita una enumeración verificada y un fallback
explícito para este dispositivo. Evitar persistir características entre cambios
del HAL/módulo o actualizaciones del sistema sin invalidación.

Para rendimiento de fotografía, no hay evidencia que justifique cambiar ahora
denoise, merge, número de frames, buffers RAW u OIS. `RamPatcher` permite alterar
parámetros nativos, pero un menor tiempo de procesamiento conseguido eliminando
frames puede reducir calidad. Debe medirse por separado del arranque.

## Qué descartan las mediciones anteriores

La traza del APK actual registró `bindApplication` 898.62 ms,
`CameraActivityController#initialize` 937.88 ms y `UiWirer#wire` 307.92 ms;
son secciones anidadas y no deben sumarse. El controlador PHOTO mostró unos
415 ms y la inflación de UI unos 334 ms. El HAL configuró sesiones en 29–57 ms
en las corridas normales. Esto orienta la investigación al arranque de la app,
pero no cuantifica todavía el escaneo 0–249.

Las pruebas de ART `speed`, inicialización eager/gate y rendimiento fijo no
mostraron mejora reproducible y se revirtieron. No conviene repetirlas como
supuestas soluciones. TTID y el mensaje de controles son métricas distintas;
el segundo no equivale a preview estable ni a fotografía lista. Los detalles y
límites están en `docs/GCAM_STARTUP_20261011.md`.

## Empaquetado y validación posterior

El Manifest declara `extractNativeLibs=true` y las bibliotecas están comprimidas
en el ZIP. Android las extrae durante la instalación: no se debe afirmar que
descomprime los 135 MB de `libgcastartup.so` en cada apertura. Cambiar solamente
la compresión del APK no demuestra un ahorro de arranque.

Una reconstrucción invalida la firma original. No se dispone de su clave y no
se ha demostrado que una refirma pueda actualizar este paquete conservando
datos. Antes de desplegar se necesita respaldo verificable de configuración y
un plan de instalación/restauración. Un hook de APatch/Zygisk, si resultase
necesario, debe vivir en un módulo exclusivo de GCam separado de RAW.

El ensayo de un parche debe comparar corridas frías intercaladas A/B con escena,
temperatura y configuración constantes, registrando TTID, primer frame de
preview y primera captura válida. Después debe verificar las tres cámaras,
RAW/JPEG, enfoque, flash SINGLE/TORCH y cambio de modos. Las métricas actuales
no permiten prometer cuántos segundos se ahorrarían.

## Documentación oficial consultada

El [análisis ampliado hasta la preview](PREVIEW_ANALYSIS_20261011.md) identifica
una dependencia síncrona de perfiles de vídeo dentro de PHOTO y distingue los
frames recibidos del sensor de la disponibilidad de la interfaz.
El [ensayo de caché de perfiles y scan6](PROFILE_RESULTS_20261011.md) documenta
el parche desarrollado, la comparación A/B/B/A y sus verificaciones y límites.

- [Android: tiempo de apertura y lazy initialization](https://developer.android.com/topic/performance/issues/launch-time).
- [Android: buenas prácticas de inicialización](https://developer.android.com/topic/performance/appstartup/best-practices).
- [Bionic: carga de bibliotecas desde APK](https://android.googlesource.com/platform/bionic/+/HEAD/android-changes-for-ndk-developers.md).

Android recomienda aplazar trabajo innecesario, identificar I/O e
inicializaciones costosas y medir la apertura completa. En este APK la aplicación
práctica de esa recomendación empieza por medir el escaneo masivo y el logging,
no por alterar los binarios MTK que ya suministran RAW funcional.
