# Apertura lenta de BSG GCam 9.7 en X6810-GL

Estado vigente: [revalidación del módulo GCam 0.2.0](GCAM_STARTUP_CURRENT.md).
El informe siguiente es histórico. La investigación inicial del
[11 de octubre](GCAM_STARTUP_20261011.md) no obtuvo mejoras; los ensayos
posteriores de DEX sí encontraron mejoras y están integrados en un módulo
independiente del módulo RAW.

Investigación por ADB del 27 y 29 de septiembre de 2026. Paquete `com.android.MGC_9_7_047`, versión `9.7.047.702121536.18`. **Resultado:** no se encontró una modificación XML o del módulo que reduzca de forma reproducible el tiempo de apertura sin comprometer funciones. El retraso medido se concentra en la inicialización de GCam y en la espera de CPU, no en la configuración de streams del HAL. El usuario precisó que la demora habitual percibida es de **5–6 segundos**; los diez segundos comunicados inicialmente eran una estimación exagerada.

## Base del dispositivo y del proyecto

- Las bibliotecas montadas correspondían exactamente a v0.11: `libmtkcam_metastore.so` SHA-256 `a05f038d7e638f597f751750cafc0e0c9d788be85588e52afbfeff9e583759d5` y `libmtkcam_pipelinepolicy.so` SHA-256 `d3bfa9aab5d43af352a3bf717ff4b399cad6744ccc2c548ef8ae4650f3635ad2`. APatch informó el módulo `x6810_raw12mp` v0.11.
- El parche de v0.11 modifica el mínimo de buffers de la colección RAW16 de la policy a `max(original, 6)`. No modifica código Java, recursos ni la secuencia de inicio de GCam. El metastore publica RAW16 y metadatos compatibles para S5KGM1ST, OV08A10 y HI1631Q. La frontal publica RAW binned de 2320×1744, no el Quad Bayer completo.
- La preferencia anterior `avc_profile_high_supported=false` permaneció intacta. Los intentos OIS, interfaz a demanda, prewarm y perfil de dispositivo se revirtieron al terminar cada ensayo. El 29 de septiembre se verificó `device_key=raven`, sin entradas experimentales OIS/interfaz/prewarm y ART en `speed-profile`.

## Qué se midió

`am start -W` y el evento `ActivityTaskManager: Displayed` miden **primera presentación de la actividad**, no imagen funcional ni controles listos. Por ello se guardaron logcat, capturas a tiempos conocidos y una traza `atrace` con las categorías de app, interfaz, cámara y planificador. Las capturas ADB pueden tardar varios segundos cuando el sistema está saturado: el archivo de cada captura corresponde a algún instante entre `begin` y `end` del resumen, no necesariamente al segundo solicitado. Android distingue formalmente primera presentación y presentación completa en su [guía de medición de arranque](https://developer.android.com/topic/performance/issues/launch-time).

| Condición | Primera presentación | Observación |
|---|---:|---|
| GCam v0.11, proceso frío, sistema ya iniciado (27/09) | 1,76–2,32 s en los dos primeros ensayos | HAL configuró en 38–80 ms; preview presente hacia la captura de 4 s. |
| Primera apertura después de reiniciar (27/09) | 5,19 s | Pantalla todavía negra en la captura solicitada a 6 s; imagen visible en la de 10 s. `configureStreams_3_6` tardó 38 ms. |
| GCam con ajustes actuales del usuario (29/09) | 2,31 s | Imagen y controles visibles en la captura solicitada a 4 s; HAL configuró en 15 ms. |
| Cámara nativa Transsion, mismo HAL v0.11 (29/09) | 1,23; 0,84; 0,76 s | Comparación de primera presentación, no ensayo idéntico de todas las funciones. |

El `logcat` de la apertura posterior al reinicio muestra dos conexiones Camera2 del ID 0, su configuración rápida, y después varios bloqueos del hilo principal: `Choreographer: Skipped 161 frames!`, seguido de otros de 65 y 43 frames. También se observó inicialización de TensorFlow Lite/OpenCL y varios codificadores AVC; `setupVideoEncoder succeeded` confirma que la corrección AVC previa sigue funcionando. La memoria disponible inmediatamente después del arranque era ~4,86 GB y el estado térmico informado era 0; esos datos no respaldan una falta de RAM ni throttling térmico como explicación de **esa** apertura. No descartan episodios distintos.

La traza `atrace` de otra apertura separó los intervalos principales de GCam:

| Bloque | Tiempo total | Ejecutando en CPU | Listo para CPU, esperando turno | Dormido/esperando operación |
|---|---:|---:|---:|---:|
| `bindApplication` | 2,982 s | 1,403 s | 0,427 s | 1,152 s |
| `CameraActivityController#initialize` | 2,978 s | 1,168 s | 0,939 s | 0,871 s |
| `UiWirer#wire`, incluido en el bloque anterior | 1,202 s | 0,497 s | 0,598 s | 0,106 s |

Los bloques se superponen por jerarquía y **no se deben sumar**. El tiempo `runnable` cuantifica contención de CPU durante esa traza. Una pila Java tomada durante el inicio situó el hilo principal en `LayoutInflater` → `Typeface.create` → `FontController`/`AssetManager`, trabajando en la interfaz de la ROM. Es una muestra puntual, no una prueba de que las fuentes consuman todo el intervalo. En el arranque posterior al reinicio también había actividad intensa de `system_server`, Google Play Services y `camerahalserver`; parte del retraso adicional puede ser contención de ese primer arranque.

Los avisos `Camera HAL package not found`, `Null OIS keys (version: 3)`, `OIS is dead`, `Gralloc4: unlock ... failed`, y `Input frame and metadata cannot be null` son reales y merecen seguimiento si se investigan fallos funcionales. Los primeros dos ocurren sin una espera de segundos antes de configurar el HAL; varios de los otros continúan **después** de que GCam ya muestra imagen. La evidencia actual no permite atribuirles los más de diez segundos de espera. La prueba de OIS descrita abajo eliminó `Null OIS keys` y no aceleró el inicio.

## Cambios ensayados y resultado

Todas las escrituras XML se realizaron con GCam detenida, un respaldo local, validación XML y lectura de verificación. No se modificó la partición `vendor` ni se reinstaló el módulo.

| Ensayo | Observación | Estado final |
|---|---|---|
| `ois_api_supported=false` | Desapareció `Null OIS keys`; presentación 1,55 s frente a 1,76 s en un control cercano. La diferencia es comparable a la variación natural y `OIS is dead` siguió. | Revertido; no se recomienda como arreglo de arranque. |
| `camera.on_demand_ui_wirer=true` | Controles alternados: 2,40 y 3,54 s; con ajuste: 2,38, 2,57 y 2,81 s. Sin ganancia repetible. | Revertido. |
| Perfil `redfin` en `device_key` frente a `raven` | Ambos perfiles dieron aperturas de ~2,15–2,51 s en pares alternados. La prueba del usuario coincide: cambiar a un perfil anterior no tuvo efecto real. | `raven` restaurado. |
| Compilación ART `speed` del APK | Tres primeras presentaciones: 2,46, 2,74 y 2,17 s; se solapan con el comportamiento normal. | `speed-profile` restaurado. |
| `camera.prewarm_viewfinder_surfaceview=true` | Dos primeras presentaciones: 2,22 y 2,07 s; controles sin ajuste: 2,15 y 2,15 s. El indicador de controles listos tampoco mejoró. | Revertido. |
| `gcam.zsl_buffer_size=3` frente al valor inicial `9` | Con 3: 2,23 y 2,17 s; con 9: 2,10 y 2,02 s. El indicador de controles listos fue 3,45–3,68 s frente a 3,29–3,36 s. Reducir el colchón ZSL no aceleró el arranque. | `9` restaurado. |

**Decisión:** no incluir ninguno de estos valores en un XML recomendado ni crear v0.12 del módulo a partir de ellos. Un parche binario en `libmtkcam_pipelinepolicy.so` para corregir una espera de inicialización Java de GCam no tiene una ruta causal demostrada y arriesgaría el RAW estable de los tres sensores. La corrección de Top Shot documentada en [GCAM_TOP_SHOT.md](GCAM_TOP_SHOT.md) es independiente y debe conservarse.

## Repetición del diagnóstico

La herramienta [collect_mgc_startup.py](../scripts/collect_mgc_startup.py) genera `am-start.txt`, `logcat.txt`, log del proceso, eventos seleccionados, capturas y `summary.json` en `dist/analysis/startup-AAAAMMDD/ETIQUETA/` (excluido de Git). No borra los datos de la aplicación ni limpia cachés. Debe ejecutarse con el teléfono desbloqueado, sin otra captura de pantalla/streaming y tras confirmar el serial con `adb devices -l`:

```powershell
python scripts/collect_mgc_startup.py --serial SERIAL --label control-1 --seconds 15 --screenshots 2,4,6,10
```

Para una apertura que supere claramente los **5–6 segundos habituales**, conservar el log **de ese mismo arranque** y comparar inicio de proceso, primera presentación, `configureStreams_3_6`, activación de controles y primera imagen. Sólo ese registro puede distinguir un retraso previo en GCam de una espera nueva del HAL. Guarda nuevas capturas privadas bajo `dist/analysis/`; esa carpeta se regenera al ejecutar la herramienta y no se incluye en Git. Los artefactos de sesiones anteriores se eliminaron en la limpieza local de octubre de 2026. No publiques logs completos, capturas, seriales ni el XML privado de preferencias.

## Validación del proyecto

Se verificaron los hashes del overlay en el dispositivo. En el host pasaron `verify_v011_raw_buffers.py` (12 rutas), `verify_v08_stream_filter.py` (60 rutas), `verify_v08_sensor_policy.py` (9 rutas), `test_v08_installer_host.py` (32 escenarios para v0.11 y su rollback), `test_module_template.py` (15 módulos) y `check_repository.py`. Son comprobaciones de consistencia del parche y empaquetado; no prueban todo el CDD/CTS Camera2 ni un tiempo máximo de apertura en todas las condiciones.
