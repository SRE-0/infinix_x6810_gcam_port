# Segunda revisión del arranque de GCam

**Actualización 0.5.0:** se difirieron tabs y suscripciones visuales del panel.
La [revisión posterior](GCAM_PANEL_OPTIMIZATION_20261011.md) identifica los
factories efectivos de codecs y el segmentador; no acredita todavía un nuevo
planificador general de ML/microvideo. Los datos siguientes son históricos.

**Actualización posterior:** el consumidor de la caché errónea quedó identificado
y corregido en el módulo 0.4.0. Ver [implementación y pruebas](GCAM_SEGMENTER_CACHE_FIX_20261011.md).
Los apartados siguientes conservan el estado y las incertidumbres de la revisión anterior.

Se conserva el APK APatch 0.3.0, SHA-256
`d4ec771a9114778f1689ee256debf128e824e1e305de499e1580667e65d227d7`.
El cambio adicional retenido es la preferencia **string**
`pref_disable_log_key=1`: desactiva el registro continuo propio de BSG.
No modifica los algoritmos fotográficos, el HAL ni el módulo. Se aplicó por
ADB/root sin reiniciar y sin ARTEMIS. El APK sigue activado desde
`modules_update`; no se verificó su promoción mediante reinicio.

## Registro continuo: cambio aplicado y medido

`com.pairip.application.Application.attachBaseContext` instancia `com.b` cuando
la preferencia vale 0 o falta. Su inicializador arranca un hilo que limpia
Downloads/MGC_CRASH_LOG/9.7.047 y ejecuta un proceso con logcat de varios buffers,
todos los niveles, redirigido continuamente a almacenamiento compartido.
El proceso hijo se observó con la configuración inicial. El diagnóstico ADB
externo funciona también con la preferencia 1.

Se comparó el mismo APK diagnóstico de 0.3.0, con los mismos eventos Java y
ART `speed`, en cuatro bloques 0/1/1/0. Tres aperturas medidas y una de
calentamiento excluida por bloque: seis aperturas por condición. Se detuvo solo
GCam entre aperturas; no se borraron datos ni cachés del sistema.

| Mediana | Registro activo (0) | Desactivado (1) | Diferencia |
|---|---:|---:|---:|
| Primera pantalla, `am start -W` | 1625 ms | 1508 ms | −117 ms (7,2 %) |
| Evento `FIRST_PREVIEW_FRAME_RENDERED`, desde onCreate | 1963,873 ms | 1837,914 ms | −125,959 ms |
| Evento `SHUTTER_BUTTON_ENABLED`, desde onCreate | 1780,014 ms | 1762,887 ms | −17,127 ms |

Son métricas distintas. Los eventos Java se normalizan al inicio de onCreate,
no al envío del intent. No deben sumarse ni compararse directamente con los
eventos desde el marcador de lanzamiento del ensayo CRC anterior. La mejora
del disparador es pequeña; no demuestra una reducción sustancial del tiempo
hasta poder tomar una foto. Hay dispersión y son solo seis muestras por condición.
Medianas TTID por bloque: 1628, 1536, 1451, 1622 ms. Ninguna de las doce
aperturas registró FATAL EXCEPTION o ANR.

Después del ensayo se restauraron la preferencia original y el APK de
distribución. Luego se aplicó únicamente la preferencia 1, con otra copia de
seguridad privada. Se verificaron lectura de la preferencia, vista previa,
ausencia de procesos hijos logcat del UID de GCam y una foto JPEG principal
3000×4000 decodificada e inspeccionada. El disparo se envió a los 3 segundos;
el archivo se observó a los 7,753 segundos, incluyendo procesamiento. Esto
es una prueba funcional, no TTFD ni una mejora demostrada de calidad.
SHA-256 del JPEG: `4f9b85c876ee835a1281110ddfa685196cae5ec423a40ad0fa10c7a9cca18764`.
La primera pantalla de verificación del APK de distribución tardó 1492 ms;
es una muestra independiente, no otro resultado A/B.

La preferencia permanece en los datos de la app; el módulo no la impone.
Para deshacer exclusivamente este cambio, conservando las otras preferencias:

```powershell
python gcam/startup/preference_trial.py restore --serial <SERIAL> --key logging --backup-dir dist/analysis/gcam-next-20261011/logging-retained
```

También se confirmó en smali un defecto del limpiador `com.b$0.a(File)`:
el índice solo avanza si `delete()` devuelve true. Un fallo puede repetir
indefinidamente el mismo archivo. No se observó ese fallo en el dispositivo
y no se cambió ese método en esta revisión.

## Error de caché del segmentador: confirmado, origen pendiente

Una instancia aislada de ftrace, con `raw_syscalls:sys_exit` filtrado a
`id == 56 && ret == -21`, confirmó un openat con EISDIR. El TID coincide con
el error nativo de GCam y con el hilo `GcaGeneric-1`. La instancia se retiró
al terminar. La opción de pila de usuario no produjo una pila utilizable;
esta traza no identifica por sí sola el llamador ni su duración.

El error muestra el directorio externo de caché como archivo de salida.
En `libgcastartup.so`, la ruta de error en 0x50af2f8 intenta leer y luego
serializar la caché en la misma ruta recibida. La escritura falla y se
registra `portrait_segmenter.cc:345`. Es un fallo real en un hilo de trabajo;
su influencia causal en la apertura y su impacto fotográfico siguen sin medirse.

Se revisaron tres entradas sin aplicar una sustitución global:

- `lqv.b()` ya entrega un archivo
  `tflite_vakunov_multi-subject_2018-06-09.fb.enc.cache` al JNI de
  `NativePortraitSegmenterInterface`. Conserva comprobación del modelo y
  fallback OpenCL/OpenGL.
- `lrl.call()` construye la configuración de `NativePortraitPreviewProcessor`;
  `lrj` añade `milk` al directorio antes de serializar la ruta.
- `iuv.b()` entrega el directorio a `NativeFaceToPortraitSegmenter`, pero su
  JNI 0x2143e80 llama a 0x509a230, que añade los nombres
  `/acatfdb.seg.smd.cache` y `/acatfdb.seg.shb.cache`. Esa entrada necesita
  un directorio; cambiarla a un archivo sería incorrecto.

`fgj` y la petición de retrato también usan APIs cuyo contrato visible es
un directorio de caché. No se alteraron sin identificar el consumidor exacto.
Los offsets anteriores pertenecen exclusivamente al ELF auditado, SHA-256
`76966e7c150dfcb2795ea5b2119827a7e90b13d8c03035dbc4de583d9d12eaa6`.

El ensayo de hooks Frida provocó un SIGSEGV durante el arranque y no produjo
evidencia válida. Se descartó, se retiró el servidor y se comprobó nuevamente
el arranque normal. `cache_io_probe.js` queda marcado como experimento retirado;
no forma parte del cambio retenido.

## Panel oculto e hilos: dependencias revisadas, sin otro parche

`nsu.a()` infla la entrada y el panel, enlaza BottomSheetBehavior, observadores,
categorías y, si corresponde, tabs/ViewPager. Después enlaza el coordinador al
layout principal, gestos, ciclo de vida y cámara. `leb.k` y otros campos tienen
consumidores incluso con el panel cerrado. `OptionsMenuView.x()` solo ajusta
estado y márgenes; no es la creación costosa de filas.

La optimización existente ya difiere las filas PHOTO. Aplazar toda la estructura
requiere una inicialización explícita en el hilo principal, estado pendiente y
validación de aperturas por toque/gesto/accesibilidad, modos y ciclo de vida.
No basta con saltar `nsu.a()` ni mover la inflación a un worker. El siguiente
trabajo del panel es separar mediciones de inflación y de suscripciones para
elegir una parte cuyo aplazamiento no invalide consumidores.

La documentación de Android exige mantener las operaciones de vistas en el
[hilo de UI](https://developer.android.com/topic/performance/threads) y recomienda
medir la ruta de arranque antes de aplazar inicializaciones en
[análisis y optimización del inicio](https://developer.android.com/topic/performance/appstartup/analysis-optimization).
El delegado GPU de LiteRT tiene restricciones de contexto EGL e hilo descritas
en su [documentación nativa](https://developers.google.com/edge/litert/android/gpu_native).
La revisión previa ya observó ejecución GPU Mali y codecs MTK activos; no hay
evidencia nueva que justifique sustituirlos o habilitar aceleradores incompatibles.

## Herramientas y evidencia

- `gcam/startup/preference_trial.py`: admite el string de logging, valida tipo,
  conserva copia y restaura solo la clave elegida.
- `gcam/startup/benchmark_logging.py`: ensayo ABBA acotado y restauración en
  `finally` de preferencia y APK APatch 0.3.0.
- `trace_cache_eisdir.py`: instancia de ftrace aislada; la captura inicial con
  buffer global se sobrescribió y no sirve para identificar este fallo.
- `native_string_refs.py` y `audit_native.py --bytes`: apoyo estático. Las
  referencias ADRP a una página no prueban por sí solas una referencia exacta.
- La evidencia privada de la sesión (resultados ABBA, trazas, mapas,
  preferencias y captura final) se eliminó de `dist/analysis/` durante la
  limpieza local de octubre de 2026. Este informe conserva el resumen y no
  publica el APK ni datos personales.

Quedan abiertos el consumidor exacto de la caché errónea, la división del panel
y la evaluación fotográfica comparativa de retrato/auxiliares/RAW. Esta revisión
no declara completadas esas tareas.
