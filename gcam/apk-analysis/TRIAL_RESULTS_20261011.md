# Pruebas de modificaciones del APK — 2026-10-11

Se construyeron y ejecutaron dos variantes del APK instalado en el X6810.
El barrido limitado a seis IDs redujo la mediana de primera pantalla (TTID)
en **207 ms, un 13,4 %**, en estas pruebas. El efecto sobre el proxy de controles
fue mucho menor: **78 ms**. No se ha resuelto ni cuantificado completamente
la demora percibida de 5–6 s hasta estar listo para fotografiar.

Al terminar quedó activo el **APK original**, con su hash verificado y sin
montajes de prueba. ART quedó en `speed-profile`. El módulo RAW no se modificó.

## Modificaciones realmente ejecutadas

| Variante | Cambio en `classes.dex` | SHA-256 del APK experimental |
|---|---|---|
| scan6 | `CameraLensesScan.scanCameraLens()`: límite 250 → 6, conserva IDs 0–5 | `e6b10095a42590e5035e6054b50653341b59436a83f7e2a950871aab5de9a1cc` |
| nolog | `com.b.StartLogging()`: retorno inmediato, desactiva ese capturador de BSG | `0ff4b60f516710c0ad9d776c5cddab30337910881f1c3f072dce338a31014849` |

`dumpsys media.camera` confirmó los dispositivos 0–5 antes de construir scan6.
Este límite corresponde únicamente al X6810 comprobado. No es una variante
genérica para otros teléfonos ni para un HAL que publique otros IDs.

El constructor de APK identifica la clase y el método en las tablas del DEX,
comprueba la instrucción original, aplica el cambio y actualiza SHA-1/Adler-32
del DEX. Valida que `classes.dex` sea la única entrada ZIP cuyo contenido cambió.
Manifest, recursos, otros DEX y bibliotecas conservan su contenido descomprimido.
El ZIP se reempaqueta, por lo que sus offsets y tamaños comprimidos pueden cambiar.

Los APK experimentales **no son actualizaciones firmadas instalables**. Se
probaron mediante un bind mount temporal en el namespace global de APatch sobre
la ruta del APK ya instalado. No se desinstaló la app, no se deshabilitó la
verificación de firmas de Android y no se escribió sobre el APK original.
El proceso de la variante compilada mapeó el APK y su `base.odex`; se guardó
`maps-scan6-compiled.txt` como evidencia de ejecución. Se usaron comprobaciones
SHA-256 antes de montar y al restaurar.

El desmontaje normal encontró lectores de recursos abiertos; se usó desmontaje
lazy del único bind mount verificado y se comprobó después el hash original y
la ausencia del montaje. No quedó instalado un módulo persistente.

## Comparación de apertura

Se hicieron 21 corridas de apertura: 18 compiladas y 3 exploratorias. Cada
corrida fuerza el cierre de GCam, espera 2 s, abre con `am start -W` y registra
8 s de logcat externo. Las corridas de comparación no toman screenshots, para
evitar cargar el arranque con `screencap`. Se forzó `speed-profile` al cambiar
de APK para reducir el efecto de usar artefactos ART de otro DEX.

| APK | Corridas compiladas | Mediana TTID | Rango TTID | Mediana proxy de controles |
|---|---:|---:|---:|---:|
| Original | 8 | 1543,5 ms | 1512–3702 ms | 2560 ms |
| scan6 | 6 | 1336,5 ms | 1248–2333 ms | 2482 ms |
| nolog | 4 | 1758 ms | 1657–1860 ms | 2926 ms |

Se incluyen **todas** las corridas compiladas, también las lentas. No se
descartaron outliers para calcular esas medianas. La corrida originalmente
etiquetada `original_compiled_02` seguía ejecutando scan6 porque el primer
desmontaje falló; se corrigió a `scan6_compiled_02` y se documentó la corrección
en su resumen, sin atribuirla al original.

Las últimas seis corridas del original estuvieron entre 1512 y 1714 ms. Las
últimas cuatro de scan6 estuvieron entre 1248 y 1393 ms. Esa repetición respalda
una mejora pequeña de TTID en este entorno. Desactivar el capturador de logs
no mejoró estas mediciones; no se recomienda integrar nolog como optimización
de apertura basándose en esta tanda.

Limitaciones: muestra pequeña, bloques secuenciales, caché de archivos caliente,
aprendizaje de perfiles y temperatura no idéntica por corrida. No se comparó
un primer arranque tras reboot. El servicio térmico mostraba estado 0 durante
la comprobación, pero eso no elimina las variaciones de frecuencia y carga.
La recompilación y el reempaquetado también pueden influir.

`ModeSwitcher WAS ALREADY ENABLED!` es un proxy de controles; **no equivale a
primer frame de preview estable, TTFD ni disponibilidad completa de captura**.
La reducción de TTID no permite prometer un ahorro del mismo porcentaje en
los 5–6 s que describe el usuario.

## Captura y conservación de sensores

Con scan6 se seleccionaron sensores usando los botones verificados en la UI.
El HAL confirmó las conexiones 0, 2 y 1, respectivamente. Se extrajeron y
decodificaron correctamente estos JPEG:

| Sensor | Archivo | Dimensiones |
|---|---|---|
| Principal | `PXL_20261011_134049569.jpg` | 3000 × 4000 |
| Telefoto | `PXL_20261011_134113554.jpg` | 2448 × 3264 |
| Frontal | `PXL_20261011_134125371.MV.jpg` | 1744 × 2320 |

La sesión principal mantuvo un stream RAW16 (`format 0x20`) de 4000 × 3000,
con seis buffers máximos HAL. La opción de guardar DNG estaba desactivada;
no se generó un DNG nuevo ni se afirma una validación de su contenido.
Los algoritmos de imagen, buffers del módulo, OIS y controles de flash no se
modificaron. No se ejecutó una nueva matriz de flash SINGLE/TORCH en esta tanda.

El sondeo de captura encontró el botón por resource ID en la UI y envió un
disparo a los 3 s de una apertura fría de proceso:

| APK | Inicio real del input | Primer JPEG final observado desde apertura |
|---|---:|---:|
| Original | 3,0004 s | 7,7005 s |
| scan6 | 3,0006 s | 7,5997 s |

Ambos JPEG se decodificaron a 3000 × 4000. La diferencia de unos 101 ms en una
sola captura por APK no demuestra mejora de procesamiento. El input puede
quedar en cola y el tiempo de archivo incluye procesamiento y guardado.
Un sondeo exploratorio previo detectó un `.pending-*` en lugar del JPEG final;
se excluyó de esta comparación, se corrigió el filtro y se repitió el original.
Los JPEG de las pruebas se conservaron en el teléfono.

## Artefactos y reproducción

Directorio privado: `dist/analysis/gcam-apk-20261011/trials/`.

- `scan6.apk`, `nolog.apk` y sus manifiestos JSON de cambios.
- `app-backup.tar`: respaldo previo de 185918464 bytes de los datos privados.
- `measurements/`: logcat, salida de `am start`, timelines y resúmenes por corrida.
- `comparison.json`: comparación completa, sin retirar corridas compiladas.
- `photos/`, `photo-integrity.json`, dumps HAL y XML de UI de los tres sensores.
- `capture-*-3s-final/`, `capture-integrity.json`: sondeos de captura final.
- `package-restored.txt`, `mountinfo-restored.txt`: estado posterior a restauración.

Código exclusivo de GCam en este directorio:

```powershell
python gcam/apk-analysis/build_scan_trial.py dist/analysis/startup-20261011/gcam-current.apk dist/analysis/gcam-apk-20261011/trials/scan6-new.apk
python gcam/apk-analysis/mount_trial.py --serial <serial> apply --apk dist/analysis/gcam-apk-20261011/trials/scan6-new.apk --expected-trial-hash <hash-del-JSON>
python gcam/apk-analysis/mount_trial.py --serial <serial> restore --expected-trial-hash <hash-del-JSON>
```

El script rechaza un APK original con un hash distinto. Después de cambiar o
restaurar se usó `adb shell cmd package compile -m speed-profile -f
com.android.MGC_9_7_047`. No hay cambios de preferencias de optimización que
persistan por estos parches.

Decisión: conservar scan6 como candidato experimental con beneficio medido
en TTID; descartar nolog como optimización de velocidad. Antes de promover un
módulo persistente separado de RAW, queda medir primer frame/obturador listo
y repetir tras reboot. La prueba actual confirma compatibilidad de captura,
no una mejora de calidad fotográfica ni una solución completa del retraso.
