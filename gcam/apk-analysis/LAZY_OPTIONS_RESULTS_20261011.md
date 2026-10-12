# Filas de opciones diferidas: resultados — 2026-10-11

La variante final está integrada en `x6810_gcam_startup` 0.2.0, separada de RAW.
Añade filas de PHOTO diferidas a la caché y scan6 anteriores, con ART `speed`.
El APK original y los datos de la aplicación se conservan.

## Cambio

El caso 9 de `kzh.run` reconstruye filas. Ahora, en PHOTO, con bottom sheet
cerrado y aún sin abrir en esa instancia de `leb`, ejecuta sólo la actualización
de estado del caso 10 existente. Conserva los cambios pendientes `x`/`y`.
La primera apertura por `leb.y` habilita la construcción y ejecuta `p()` antes
de mostrar el panel. `ldz.b` garantiza también la construcción al expandir por
gesto o accesibilidad. Después se mantiene el comportamiento original; otros
modos no se difieren. Los cuerpos originales permanecen detrás de wrappers.

Estructura, referencias, listeners, tabs y coordinador se conectan al inicio.
Las vistas siguen en main. No cambian parámetros de procesamiento fotográfico.
**La primera apertura del panel paga el trabajo aplazado**; no se midió aparte
su latencia óptica.

## Mediciones

Control: caché + scan6 sin filas diferidas. Process-cold A/B/B/A, calentamiento
excluido por bloque, mismos eventos de timing y datos. No se borraron caches
ni se controlaron temperatura, DVFS o procesos ajenos. Cuatro corridas por
variante en cada ensayo; muestra pequeña, sin significancia estadística acreditada.

| Ensayo y métrica, medianas | Control | Filas diferidas | Diferencia |
|---|---:|---:|---:|
| V1, speed-profile: controlador | 768,7 ms | 680,7 ms | −88,0 ms |
| V1, speed-profile: evento de preview | 2270,5 ms | 2451,8 ms | +181,3 ms |
| V1, speed-profile: disparador habilitado | 2279,8 ms | 2286,6 ms | +6,8 ms |
| V2, speed: controlador | 679,2 ms | 548,3 ms | −130,9 ms |
| V2, speed: evento de preview | 2217,1 ms | 2034,1 ms | **−182,9 ms (8,3 %)** |
| V2, speed: disparador habilitado | 2140,4 ms | 1986,3 ms | **−154,0 ms (7,2 %)** |
| V2, speed: TTID | 1245,5 ms | 1199,0 ms | −46,5 ms |

V1 no se conservó: reducir el controlador no mejoró la preview. El segundo
ensayo usa `speed` en ambos APK; V2 añade además la salvaguarda del callback.
No es un diseño factorial: no atribuimos toda la diferencia entre ensayos
exclusivamente a ART. La mejora incremental de V2 se acredita frente al
control compilado **también** con `speed`.

Los eventos se estiman respecto al marcador ADB combinando timestamps de log
y reloj monotónico de la app. No equivalen a TTFD, toque físico o verificación
óptica del primer frame. TTID es otra métrica. No sumar estos ahorros a los de
ensayos anteriores en otras condiciones.

No hubo excepciones fatales ni ANR en las 16 corridas completas incluidas.
El último bloque de control V2 se interrumpió por un log global incompleto,
terminado antes de registrar todos los eventos; hubo desconexiones USB durante
esa fase. Se conservaron los artefactos y se repitieron las dos mediciones del
bloque final tras estabilizar el cable. La corrida incompleta no se contabiliza
como éxito ni como tiempo de arranque.

## Verificación de la release sin instrumentación

- Preview y disparador operativos en screenshot solicitado a 3 s, adquirido
  hasta aproximadamente 5 s: no acredita un límite exacto de 3 s.
- Primera apertura del panel por toque y gesto después de arranque frío.
- General: mismas etiquetas y opciones que el control, sin diferencias en
  la comparación de jerarquías. Pro: RAW/JPEG y selección de lente presentes.
- Google AWB off → on verificado y restaurado a off; comprobado tras otro
  arranque frío. Panel operativo con principal, frontal y telefoto.
- JPEG principal 3000×4000, frontal 1744×2320 y telefoto 2448×3264.
- Captura fría con toque solicitado a 2,3 s: entrada entre 2,30 y 2,44 s,
  archivo observado a 6,90 s. Incluye procesamiento y posible cola; no es TTFD.
- PHOTO → interfaz de vídeo con Start video habilitado → PHOTO, seguido de
  otro JPEG principal. No se grabó un nuevo clip en este ensayo.

No se acredita mejor calidad, enfoque del telefoto, RAW/DNG, flash ni todos
los modos. No se modificaron HAL ni módulos RAW.

## Artefactos y reproducción

Binarios, logs, fotos y XML privados: `dist/analysis/gcam-lazy-options-20261011/`.

| Artefacto | SHA-256 |
|---|---|
| Control instrumentado | `52120fc1bafcb5e2f59509af1e1b41bb9772a000d625d3248bb044bd0972c96e` |
| V1 instrumentada | `9b388047840210d8ca612f870c957ce2048dbc09716e7e4f034f152a738986ca` |
| V2 instrumentada | `ea385ffe89a6342e7b2c2ba2ac3a40e7a4533d8d67dcdf69582ab6b1e8639fd3` |
| V2 release activa | `628012f407d7df89b6d7064cc5be6e103d4a0652de7123ddddd4a2295b17759d` |

`prepare_lazy_options_trial.py` modifica sólo `kzh.smali`, `leb.smali` y
`ldz.smali` sobre la base optimizada. Ensamblar con `AssembleSmali.java`, añadir
scan6 con `combine_profile_scan.py` y empaquetar con `repack_dex_trial.py`, que
verifica checksums, referencias y que sólo cambien classes.dex y classes2.dex.
`prepare_lazy_options_release.py` elimina el helper de eventos y restaura mqt
original. La release tiene 65461 referencias en el DEX principal y 64068 en
el secundario. Scripts Python compilados y checks de higiene ejecutados.

Resultados: `lazy-summary.json` y `lazy_v2_speed_complete-summary.json`. El
segundo combina seis corridas completas iniciales y dos del bloque final
repetido en `lazy_v2_speed_tail2-results.json`, sin alterar los JSON originales.
`run_lazy_options_benchmark.py` acepta modo ART y bloque final de recuperación;
su finally restaura el módulo conservado, siempre que ADB esté conectado.
`collect_mgc_startup.py` registra ahora logcat-health.json para diagnosticar
la terminación prematura del logger.

## Instalación

0.2.0 se instaló mediante el CLI APatch y se activó con service.sh. Verifica
dispositivo, hashes y propiedad del montaje, compila con speed y restaura si
falla. No se desactiva la verificación de firmas ni se reinstala con otra firma.
APatch mantiene la actualización en modules_update hasta el próximo reinicio.
Servicio probado en esta sesión; **no se probó un reinicio real**.
[Construcción y restauración](../apatch-startup/README.md).
