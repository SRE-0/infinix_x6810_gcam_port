# Caché GPU del segmentador: módulo 0.4.0

Se corrigió la ruta de serialización del segmentador de retrato en
`libgcastartup.so`. El módulo APatch 0.4.0 conserva el APK de 0.3.0 y añade una
biblioteca con una sola instrucción modificada. Instalado y activado directamente
en X6810-GL, Android 16 GSI, sin reiniciar y sin ARTEMIS.

## Causa comprobada y cambio

La sonda Java temporal registró la ruta que `lqv.b()` entrega al JNI:

```text
/storage/emulated/0/Android/data/com.android.MGC_9_7_047/cache/tflite_vakunov_multi-subject_2018-06-09.fb.enc.cache
```

El error se produjo dentro de esa llamada `tkn.initSegmenter`, en el mismo TID
de trabajo. Java proporciona correctamente el archivo. El constructor nativo
en 0x4618ab4, al preparar el motor de inferencia, obtiene sus datos y longitud
en x0/x1 y llama a `dirname` (0x5f1d6dc) desde 0x4618e68. Copia ese resultado
a la configuración y lo pasa como archivo al método Init del motor. Este
intenta leer/escribir la caché en el directorio raíz: openat devuelve EISDIR,
seguido de `Failed to updated cache` y `Could not initialize inference engine`.

Se reemplazó exclusivamente ese BL por NOP: x0/x1 conservan el nombre completo
que copia el código posterior. El helper dirname genérico y sus otros llamadores
siguen intactos. El cambio abarca cuatro bytes, `1d126494` → `1f2003d5`, con
igual tamaño de archivo y comprobación SHA-256 del ELF original antes de editar.
Los modelos, parámetros de precisión, delegados, hilos, símbolos y código de
inferencia conservan sus valores. El constructor afectado mantiene su tratamiento
original de una ruta ausente/vacía y de la caché inválida.

| Componente | SHA-256 |
|---|---|
| APK conservado, 0.3.0 | `d4ec771a9114778f1689ee256debf128e824e1e305de499e1580667e65d227d7` |
| Native original | `76966e7c150dfcb2795ea5b2119827a7e90b13d8c03035dbc4de583d9d12eaa6` |
| Native corregido | `64cfcb3f598cdf3e75875bdd4cb8e8775a6763be15c3d2240d1d7ee0656f053a` |
| ZIP APatch 0.4.0 | `bb70fcf08b5faa2a2be6813e44aa02f471b8eb82bf29b96b5c4055182f960c23` |

La caché generada ocupa aproximadamente 92 KB; empieza con el identificador
FlatBuffer AFCM y contiene identificación del driver OpenCL. Su reutilización
se comprobó por la reducción reproducible del tiempo de inicialización y por
regeneración tras retirarla/truncarla. El motor puede reescribirla en cada
ejecución: el SHA o mtime no tienen que permanecer constantes.

La [documentación primaria de TensorFlow](https://github.com/tensorflow/tensorflow/blob/master/tensorflow/lite/g3doc/performance/gpu.md#reducing-initialization-time-with-serialization)
describe el uso de datos y kernels guardados para evitar recompilación al
inicializar el delegado GPU. Es contexto para el mecanismo; la identificación
de este defecto específico procede del binario y del dispositivo. El contrato
de `serialization_dir` en el delegado público sigue siendo un directorio: este
parche corrige el archivo de caché del wrapper de inferencia de GCam, no cambia
globalmente aquel contrato.

## Comparación con reversión

Se usó un mismo APK temporal con 193 sitios Java instrumentados, ART `speed` y
`pref_disable_log_key=1`. Solo se alternó la biblioteca nativa original/corregida.
Cuatro bloques A/B/B/A: dos aperturas medidas y una de calentamiento excluida por
bloque, cuatro muestras por variante. Aperturas con proceso detenido y sistema
de archivos caliente; la caché válida ya existía al medir B.

| Mediana | Original | Corregido | Diferencia |
|---|---:|---:|---:|
| Duración de `initSegmenter` en el worker | 4109,066 ms | 776,190 ms | −3332,876 ms (81,1 %) |
| Fin de esa llamada desde onCreate | 6177,200 ms | 2790,535 ms | −3386,665 ms |
| Primera pantalla, `am start -W` | 1531,5 ms | 1441,5 ms | −90 ms |
| Primer frame renderizado, evento desde onCreate | 1836,930 ms | 1741,124 ms | −95,806 ms |
| Disparador habilitado, evento desde onCreate | 1702,527 ms | 1586,804 ms | −115,723 ms |

El ahorro de 3,33 segundos pertenece al segmentador en segundo plano. No es
un ahorro de 3,33 segundos en la apertura total. En las ocho muestras, la entrada
a `initSegmenter` ocurrió después del primer frame y del disparador habilitado:
1844–2462 ms desde onCreate en A y 1968–2035 ms en B. Por tanto, las diferencias
anteriores de TTID/vista previa/disparador son observaciones del ensayo que
**no demuestran un efecto causal de este parche en la apertura inicial**.
La mejora comprobada es la inicialización del motor y su caché. Son cuatro
muestras por variante y no se midió la latencia de un primer disparo inmediato
en Retrato con una persona.

Los errores de escritura/inicialización aparecieron en 4/4 aperturas A y 0/4 B.
Al volver a A reaparecieron pese a existir ya el archivo válido. No hubo
FATAL EXCEPTION, Fatal signal ni ANR en las ocho aperturas medidas. B ejecutó
`dummyImageProducesReasonableMask` y no entró en la segunda inicialización Java
de fallback OpenGL. La creación inicial sin caché tardó 4268,885 ms: generar
los datos por primera vez conserva un coste alto.

## Recuperación y módulo

Cuatro comprobaciones con copia íntegra de la caché derivada y restauración
final verificada por SHA-256:

| Estado | Inicialización | Resultado |
|---|---:|---|
| Archivo ausente | 4264,944 ms | Caché AFCM regenerada, sin errores de escritura/inferencia |
| Reapertura | 808,455 ms | Reutilización, sin fallo nativo |
| Archivo truncado a 15 bytes inválidos | 4255,347 ms | Caché regenerada, sin fallo nativo |
| Reapertura | 685,387 ms | Reutilización, sin errores |

La prueba previa abortó antes de modificar el teléfono por una comprobación
de lectura del formato; solo la ejecución `native-cache-recovery-v2` es válida.
Todas las pruebas temporales restauraron los montajes y datos respaldados.

El módulo monta `payload.apk` y `native.so` sobre los archivos del paquete
instalado, en el namespace global de APatch. La biblioteca dentro del ZIP del
APK permanece original; la biblioteca efectiva en ejecución es el montaje
separado sobre `lib/arm64/libgcastartup.so`. Los originales en disco se conservan.

La activación comprueba dispositivo, ambas entradas y payloads, hashes y
propiedad por dispositivo/inodo. Verifica todos los caminos antes de montar,
compila el APK con ART `speed` y revierte los montajes nuevos ante fallo.
`restore` comprueba ambos propietarios antes de retirar cualquiera.
Se verificaron apply, apply repetido, restore de ambos archivos con hashes
originales, y una nueva activación. La versión está en `modules_update`;
la promoción y activación automática tras reinicio quedan pendientes por
la instrucción del usuario de no reiniciar.

```powershell
python gcam/apatch-startup/build.py dist/analysis/gcam-crc-20261011/crc-release.apk dist/analysis/gcam-next-20261011/x6810-gcam-startup-0.4.0.zip --native dist/analysis/gcam-next-20261011/libgcastartup-cache.so
adb shell su -M -c '/system/bin/sh /data/adb/modules_update/x6810_gcam_startup/activate.sh status'
adb shell su -M -c '/system/bin/sh /data/adb/modules_update/x6810_gcam_startup/activate.sh restore'
```

El constructor rechaza sobrescribir el ZIP existente. Para actualizar el módulo
hay que restaurar con el script de la versión activa antes de reemplazar los
payloads. Después de una promoción real, corresponde la ruta `modules`.
El ajuste de registro de BSG es independiente y sigue en 1.

## Panel de opciones: nueva medición

Dos aperturas diagnósticas del original permitieron emparejar 146 llamadas
ejecutadas por sitio y TID, sin pares abiertos ni desordenados. El panel mostró:

- Inflación principal: 62,227 y 40,970 ms.
- Un recorrido de elementos y suscripciones: 44,259 y 51,770 ms.
- `nte.a()`: 26,135 y 22,995 ms.
- Construcción de cada tab: aproximadamente 10–19 ms, más sus enlaces.

Estas mediciones incluyen el coste pequeño de registrar cada par y sirven
para priorizar. Todavía no se aplazaron suscripciones ni construcción del
panel: se deben revisar los consumidores de estado y la primera apertura.

## Evidencia privada y herramientas

Las sondas Java, pares por llamada, desensamblado, ABBA, recuperación,
cachés de prueba, logs y resultados se guardaron en
`dist/analysis/gcam-next-20261011/` y se eliminaron durante la limpieza local
de octubre de 2026. Este informe conserva las conclusiones resumidas. La sonda
no forma parte del payload publicado; el APK 0.3.0 y la biblioteca corregida
se incorporaron al módulo 0.4.0.

- `prepare_remaining_probe.py`: copia aislada, llamadas estáticas sin registros
  nuevos y respeto de `move-result` adyacente.
- `patch_segmenter_cache.py`: parche nativo con hash y bytes esperados.
- `mount_native_trial.py`: montaje temporal con guardas de hash y propietario.
- `benchmark_native_cache.py`, `summarize_native_cache.py`: comparación ABBA.
- `verify_segmenter_cache.py`: recuperación acotada de la caché derivada.

## Capturas del módulo de distribución

Con ambos payloads 0.4.0 montados y sin la sonda Java se verificaron vista previa
y cuatro archivos JPEG decodificados completamente:

| Prueba | Resolución | Archivo |
|---|---|---|
| PHOTO principal, apertura con proceso detenido | 3000×4000 | `PXL_20261011_230939046.jpg` |
| Modo Retrato, captura con app abierta | 3000×4000 | `PXL_20261011_231106198.PORTRAIT.ORIGINAL.jpg` |
| PHOTO frontal | 1744×2320 | `PXL_20261011_231143269.jpg` |
| PHOTO telefoto | 2448×3264 | `PXL_20261011_231437842.MV.jpg` |

Se inspeccionaron visualmente la foto principal y la telefoto. La muestra tele
está desenfocada y no permite evaluar nitidez; la selección de 4.9 y la salida
de 8 MP sí quedaron verificadas. El modo Retrato produjo el original de una
escena sin sujeto humano; no demuestra separación de personas ni mejora de
bokeh. No se demostró una mejora de calidad de imagen con escena controlada.

La foto principal recibió el input a los 3 segundos y el archivo se observó
a los 7,935 segundos, incluyendo procesamiento. No es TTFD. La comprobación
independiente de primera pantalla dio 1521 ms; es una muestra de distribución,
no otra comparación A/B. Ninguno de los logs finales de captura y arranque
contenía los errores de caché/inferencia, FATAL EXCEPTION, Fatal signal ni ANR.
Al terminar se dejó PHOTO principal seleccionado, con el registro BSG en 1.
Los hashes y tamaños de los archivos quedan en `photos040.json`, bajo dist.

No se volvieron a validar RAW/DNG, flash, vídeo grabado ni retrato humano en
esta tanda. Esos componentes mantienen su implementación anterior.
