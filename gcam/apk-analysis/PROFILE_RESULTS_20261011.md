# Ensayos de caché de perfiles y escaneo — 2026-10-11

Se desarrolló y probó un parche que evita repetir consultas de perfiles de
vídeo durante la construcción del controlador PHOTO. Combinado con el escaneo
limitado a los seis IDs de cámara de este X6810, adelantó el evento de preview
aproximadamente **600 ms** y la habilitación del disparador **637 ms** en la
comparación A/B/B/A realizada en el dispositivo.

Son mejoras de latencia observadas en una muestra pequeña; no se declara
resuelto todo el retraso de 5–6 segundos ni una mejora de calidad fotográfica.

## Original y componentes modificados

El APK aportado en `gcam/MGC_9.7.047_V32_MGC.apk` coincide con el instalado y con
la extracción analizada. SHA-256:
`132e18273b3aafdb93e851f5db88156bd4f82c5032ad8de6594fa5a49ea6fe89`.
La extracción original y ese archivo permanecen intactos.

La modificación principal afecta a `hir.J(pui)` y a dos consultas dentro de
su constructor privado de listas. Se conserva el cuerpo original, con otro
nombre privado, y un wrapper de la firma original abre/cierra una caché por
invocación. `ProfileScope` usa `ThreadLocal` y elimina la caché también si se
propaga una excepción. No se modifica el Map persistente de `hir` ni se añade
concurrencia a ese Map.

Durante una llamada de `hir.J`, las seis listas usan el mismo `pui`. Se reutiliza:

- `CamcorderProfile.hasProfile`: por calidad numérica, incluyendo resultados
  negativos. El código original podía consultar 78 veces nueve calidades.
- `osh.aW`: por objeto `pgf`, conservando sus variantes y la lógica BSG original.
  El resultado `pgh` es inmutable; el filtro `pfw.e` solamente lo lee.

La caché se descarta al terminar cada llamada, incluso en un hit de la caché
original de `hir`. No sobrevive a una inicialización posterior, cambio de
cámara o preferencias. No se observaron llamadas recursivas a `hir.J` dentro
del cuerpo original. Las seis listas, su orden, filtros y valores no se cambian.
El ensayo reduce trabajo antes de intentar trasladarlo a otro hilo: no hay
esperas bloqueantes añadidas desde UI hacia workers.

El parche combinado cambia además el límite de `scanCameraLens` de 250 a 6.
Se verificó nuevamente en `dumpsys media.camera` que el dispositivo expone
seis dispositivos HAL, IDs 0–5. Es una restricción específica de este teléfono;
no debe distribuirse como parche universal para otros dispositivos.

No se cambiaron bibliotecas MTK, recursos, Manifest, providers, lógica de
integridad, procesamiento fotográfico ni módulos RAW/APatch. Sólo difieren
`classes.dex` y `classes2.dex`; el repacker verifica todas las demás entradas
ZIP y las sumas y límites de referencias de los DEX.

## Comparaciones

Los APK de referencia y ensayo contienen exactamente el mismo DEX secundario,
incluidas las mismas marcas de `CameraActivityTiming`. La referencia reconstruye
el DEX principal sin el parche. Se aplicaron por montaje temporal con root al
paquete existente, conservando datos; ART `speed-profile` informó `Success`
antes de cada cambio de variante.

Cada comparación siguió A/B/B/A. Se excluyó una corrida de calentamiento por
bloque. Cada lanzamiento medido hizo `force-stop`, esperó dos segundos y observó
siete segundos, sin screenshots ni ftrace concurrentes. No se borraron datos,
logs o cachés. No se controlaron temperatura, DVFS o caché del sistema de archivos:
la muestra es process-cold con filesystem caliente.

### Caché sola

Se recogieron 12 corridas medidas: seis por variante. Se excluyó
`cache_abba_g4_baseline_2` porque coincidió con un `dumpsys media.camera` de
diagnóstico. Se conserva íntegra para auditoría. Estadísticas de cinco corridas
de referencia y seis con caché, medianas:

| Métrica | Referencia | Caché | Diferencia |
| --- | ---: | ---: | ---: |
| Inicialización del controlador | 1074,4 ms | 866,7 ms | −207,8 ms |
| Disparador habilitado desde marca ADB | 3102,7 ms | 2957,1 ms | −145,6 ms |
| Evento de preview de Activity desde marca ADB | 3272,0 ms | 3115,7 ms | −156,3 ms |
| TTID de `am start -W` | 1746 ms | 1768 ms | +22 ms |

El resultado de la caché afecta a la preparación posterior de PHOTO. No se
presenta el TTID como mejora de esta variante.

### Caché y scan6

Ocho corridas medidas, cuatro por variante, sin exclusiones; medianas:

| Métrica | Referencia | Combinado | Diferencia |
| --- | ---: | ---: | ---: |
| TTID | 1696,0 ms | 1297,5 ms | −398,5 ms (23,5 %) |
| Primera imagen recibida desde marca ADB | 1719,6 ms | 1311,0 ms | −408,5 ms |
| Inicialización del controlador | 1064,3 ms | 832,9 ms | −231,4 ms |
| Disparador habilitado desde marca ADB | 3065,7 ms | 2428,4 ms | −637,3 ms (20,8 %) |
| Evento de preview de Activity desde marca ADB | 3213,5 ms | 2613,9 ms | −599,6 ms (18,7 %) |
| Activity estable desde marca ADB | 3854,6 ms | 3316,6 ms | −537,9 ms |

El rango del evento de preview fue 2988–3380 ms para la referencia y
2577–2677 ms para el combinado. No hubo `FATAL EXCEPTION` ni `ANR in` en los
logs de las corridas medidas.

La marca ADB se escribe antes de lanzar la Activity. La estimación hasta cada
evento combina el timestamp de log de `onCreate` con los intervalos del reloj
monotónico de la app. Incluye overhead de host/ADB; no es latencia desde un toque
físico. El evento de Choreographer de la Activity, el frame VFE y el disparador
son señales distintas, no una medición de píxeles físicos ni `reportFullyDrawn`.
No se suman spans anidados para estimar el ahorro.

## Versión sin marcas de diagnóstico y comprobaciones funcionales

Se construyó otro DEX secundario desde la extracción original añadiendo sólo
`ProfileScope`; no contiene `StartupTimeline` ni cambios al recorder `mqt`.
Se montó y compiló en el dispositivo. Una apertura adicional informó TTID
1296 ms y el screenshot solicitado a los cuatro segundos mostró preview y
controles operativos. Esa corrida aislada no reemplaza la comparación anterior.

Se obtuvieron y decodificaron JPEG de:

- Principal: 3000×4000; en una apertura fría con input de disparador solicitado
  a los tres segundos se produjo una foto.
- Telefoto: 2448×3264, después de seleccionar el control `ID1`.
- Frontal: 1744×2320, después de `Switch to front camera`.
- Principal después de vídeo: otra captura JPEG al volver a PHOTO.

La preview principal y las fotos de tele/frontal se inspeccionaron visualmente.
La foto del tele está desenfocada en la escena cercana. Esto demuestra producción
del JPEG, no enfoque correcto ni ausencia de regresiones de calidad. No se
compararon fotografías de una escena fija con el original.

Se grabó vídeo 1080p, se detuvo y se volvió a PHOTO. El archivo MP4 de 60.714.031
bytes tiene contenedor válido, pista H.264 `avc1` 1920×1080, 1009 muestras,
42,04 s y promedio de 24,00 fps; contiene pista de audio `mp4a` de 42,01 s.
Se verificaron estructura y metadatos, no se decodificaron todos los frames ni
se comparó la fluidez/audio con el original.

Durante la grabación UIAutomator no logró obtener un estado idle. Se detuvo
mediante coordenadas verificadas en un screenshot actual del botón Stop. El
helper UI se corrigió para rechazar dumps fallidos en vez de leer un XML viejo.

No se hicieron nuevas pruebas de DNG, flash SINGLE/TORCH, OIS, todos los FPS,
cámaras virtuales o estrés prolongado. No se atribuye una mejora fotográfica a
estas pruebas de latencia y funcionamiento básico.

## Artefactos y reproducción

Código reproducible aislado en `gcam/apk-analysis/`:
`prepare_profile_trial.py`, `ProfileScope.smali`, `combine_profile_scan.py`,
`prepare_profile_release.py`, `run_profile_benchmark.py` y
`summarize_profile_trials.py`. Los helpers de ADB y contenedor son
`device_ui.py`, `capture_probe.py` e `inspect_mp4.py`.

Los DEX, APK, JSON de tiempos, logs, fotos y vídeo permanecen privados bajo
`dist/analysis/gcam-profile-trial-20261011/`. Las estadísticas definitivas son
`cache_abba-summary.json` y `combined_abba-summary.json`. Las corridas de
calentamiento y la exclusión también se conservan.

El candidato sin registro adicional es `profile-cache-scan6-release.apk`.
SHA-256:
`83d8f56956bd6ad35430636591b672090f065486fcc6f76e1e964a6c05ca763b`.
Es un APK experimental reconstruido: conserva entradas de firma antiguas pero
no es una actualización firmada instalable con `adb install -r`. Su validación
se realizó mediante el montaje root temporal, sin deshabilitar verificaciones
del sistema. No se creó un módulo persistente ni se incorporó al módulo RAW.

Para repetir la comparación combinada usando los artefactos existentes:

```powershell
python gcam/apk-analysis/run_profile_benchmark.py --serial SERIAL --directory dist/analysis/gcam-profile-trial-20261011 --prefix NUEVO_PREFIJO --runs 2 --trial-variant profile-cache-scan6
python gcam/apk-analysis/summarize_profile_trials.py dist/analysis/gcam-profile-trial-20261011 --prefix NUEVO_PREFIJO
```

Para probar únicamente el candidato, utilizar `mount_trial.py apply` con su
hash anterior, comprobar `cmd package compile ...` y terminar con
`mount_trial.py restore --expected-trial-hash ...`. La aplicación queda
force-stopped tras restaurar. El runner automatiza esa restauración en `finally`.

## Estado al terminar

APK original restaurado, hash verificado y sin montajes de ensayo. ART volvió
a compilar con `Success`. Se retornó a PHOTO con la cámara principal antes de
restaurar. Las fotos/vídeo se conservan como evidencias privadas; no se borraron
datos de GCam ni se alteraron los módulos RAW/APatch.

Las herramientas Python pasan `py_compile`; se ejecutó la comprobación de
higiene del repositorio y de sus dos módulos. El siguiente trabajo con evidencia
pendiente es reducir inicialización redundante de UI y validar la publicación
segura de datos si se ensaya preparación real en segundo plano. Android distingue
[TTID de la apertura completa](https://developer.android.com/topic/performance/issues/launch-time)
y recomienda medir el
[trabajo costoso del hilo principal](https://developer.android.com/topic/performance/appstartup/analysis-optimization).
