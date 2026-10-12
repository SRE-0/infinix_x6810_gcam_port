# Diagnóstico del arranque hasta la preview — 2026-10-11

El retraso observado está concentrado en la preparación de la aplicación y de
su interfaz. El sensor ya entrega imágenes mientras el hilo principal todavía
construye el controlador PHOTO. Se identificó y midió una dependencia concreta:
PHOTO calcula sincrónicamente una matriz de capacidades de vídeo.

Esto explica una parte del retraso, no demuestra todavía una solución ni permite
atribuir todos los 5–6 segundos reportados a una sola función.

## Alcance y método

Paquete `com.android.MGC_9_7_047`, versión `9.7.047.702121536.18`, en X6810-GL
con Android 16 GSI. Se revisaron el inventario del APK completo, Manifest y
providers, Application, grafo de inicialización, código BSG, carga nativa,
controlador PHOTO, recursos e interfaz. El análisis dinámico se concentró en
las rutas que realmente ejecutan las aperturas frías. No se afirma haber
auditado exhaustivamente cada método de las aproximadamente 17.000 clases.

JADX contiene errores de decompilación; las rutas decisivas se verificaron en
smali. `defpackage` es una agrupación de JADX: esas clases no tienen ese prefijo
en el DEX.

Se construyeron dos APK de diagnóstico con marcas de reloj monotónico y
registro de los eventos existentes de `CameraActivityTiming`. Las modificaciones
no cambiaron la política de cámara, preferencias ni bibliotecas nativas. Se
ensayaron mediante montaje temporal del APK con root y se compiló ART con
`speed-profile`, verificando `Success` antes de ejecutarlos. No se alteró la
verificación de firmas ni la lógica de integridad de Pairip. La instrumentación
introduce sobrecarga: estos tiempos sirven para localizar trabajo, no son una
comparación de rendimiento A/B de una optimización.

## Trabajo costoso demostrado

| Ruta | Medición | Interpretación |
| --- | --- | --- |
| `CameraApp.onCreate → CameraLensesScan.<init>` | 451–473 ms, APK diagnóstico V2 | Escaneo síncrono anterior a la Activity, en el hilo principal. |
| `jpq.a → kid.b` | 320–419 ms, V2 | Dependencia de PHOTO, también en el hilo principal. |
| `kid.b → hir.J(pui)` | 316–408 ms, V2 | Prácticamente todo el bloque anterior está aquí; ambos tiempos son anidados. |
| Seis llamadas de `hir.J` al constructor de listas de perfiles | 45–78 ms cada una, V2 | En conjunto 315–407 ms; no se suman otra vez al tiempo de `hir.J`. |
| `UiWirer#wire` | 378 ms original; 395–401 ms V2 | Conexión de interfaz en el hilo principal. |
| `cameraUiModule#inflate` | 383 ms original | Inflación de interfaz durante `onCreate`. |
| `CameraAppUI#init` | 183 ms original | Incluye `updateOptionsBar` de 163 ms; no son costes independientes. |

La ruta nueva y prioritaria es:

```text
setModuleFromMode PHOTO
  getModuleController
    jpq.a()
      kid.b()
        hir.J(cameraId)
          seis listas de perfiles de vídeo
            CamcorderProfile.hasProfile(...)
            osh.aW(...) → CamcorderProfile.get(...) o perfil BSG
```

`hir.J` guarda el resultado por cámara en un Map. Cuando no hay entrada, llama
seis veces a `mb4c07af49db6252411e985c2793`, con distintos `pfp`. Cada llamada
recorre los 13 valores de `pgf`. El código contiene, por tanto, 78 oportunidades
de consultar `hasProfile` por fallo de caché, con calidades repetidas; `get`
depende de qué perfiles estén disponibles y de las preferencias BSG. No se
instrumentó individualmente cada consulta JNI: todavía no se atribuye un tiempo
exacto a `hasProfile`, `get` o sus alternativas BSG.

La primera instrumentación V1 dejó un hueco repetido de 288–293 ms alrededor de
esta dependencia. V2 midió directamente `kid.b`, `hir.J` y las seis listas,
confirmando la ruta. El constructor real de `jpp` fue de aproximadamente 1,3 ms
en V1: el coste no se debe principalmente a ejecutar su constructor.

## El sensor entrega frames antes de que la app esté lista

Tiempos relativos a `ACTIVITY_ONCREATE_START`, no a pulsar el icono:

| Evento | V2 sin ftrace | V2 con ftrace |
| --- | ---: | ---: |
| Fin de `onCreate` | 459 ms | 453 ms |
| Primera imagen recibida | 809 ms | 644 ms |
| Primer frame renderizado por VFE | 911 ms | 785 ms |
| Inicio de inicialización del controlador | 906 ms | 809 ms |
| Fin de inicialización | 2397 ms | 1964 ms |
| Disparador habilitado | 2634 ms | 2108 ms |
| Evento de primer frame renderizado de la Activity | 2919 ms | 2317 ms |
| Activity estable | 3646 ms | 3005 ms |

La diferencia entre recibir una imagen y registrar el frame de la Activity fue
de aproximadamente 1,67–2,11 segundos. VFE, callback de Choreographer y retirada
de la cubierta son señales distintas; ninguna por sí sola demuestra el instante
exacto en que un píxel aparece físicamente en la pantalla.

La traza del APK original, sin marcas nuevas, confirma el patrón: desde
`bindApplication`, primera imagen a 1560 ms, primer frame VFE a 1663 ms,
inicialización del controlador entre 1661 y 2725 ms, y construcción del módulo
PHOTO de 309 ms. El TTID informado por `am start -W` fue 1695 ms: no mide una
cámara plenamente utilizable. Los 5–6 segundos no se reproducen idénticamente
en todas las aperturas; estas medidas incluyen aperturas más rápidas y no deben
presentarse como una eliminación de ese problema.

## Hipótesis descartadas o todavía sin evidencia suficiente

- El coste medido de permisos y espera de dispositivos fue pequeño frente al
  trabajo de UI/controlador. El HAL ya suministraba imágenes antes de finalizar
  este trabajo; estas corridas no justifican modificar el módulo RAW.
- `Application.attachBaseContext` contiene Pairip/RamPatcher. Las operaciones
  observadas de RamPatcher, VMRunner e integridad duraron unos pocos milisegundos
  en V1; no explican el bloque repetido de PHOTO.
- Existe un límite de 4000 ms en la cadena de readiness y un fallback de cubierta
  de 4000 ms. No se observó su expiración como causa del arranque medido. La ruta
  `nki.q` que programa el fallback no apareció en estas aperturas frías.
- `IC.hideRequestFromApi` corresponde al teclado/InsetsController de Android,
  no a la cubierta de la cámara. Su duración no es evidencia de una espera de
  preview de cuatro segundos.
- Carga nativa, MediaCodec y procesamiento fotográfico deben seguir verificándose
  si otras aperturas presentan otro patrón. No hay evidencia actual para eliminar
  providers o trasladar toda la UI a un worker.

## Calidad de las trazas y artefactos

La traza V1 de 8192 KB perdió eventos: 1.215.253 conservados frente a 1.304.768
escritos. Sus spans anidados no se usan para cuantificar fases. Los marcadores
directos del log son una fuente distinta. Una transferencia anterior de 74 bytes
también se descartó como traza inválida.

Se aumentó el buffer a 32768 KB y se corrigió la transferencia mediante ADB.
V2 conserva 1.014.665/1.014.665 eventos; el original conserva
858.585/858.585. En V2 `CameraActivity#onCreate` de ftrace dura 453,264 ms frente
a 453,151 ms en las marcas directas, corroborando la correlación. El vendor
todavía informa un error de `record-tgid`; el recolector exige `tracing_on=1`,
pero no declara una configuración de trazado completamente limpia.
El importador también reportó 214 errores `systrace_parse_failure` en la traza
original. Conservar todos los eventos del buffer no equivale a una importación
sin errores; se mantienen los logs del procesador y se usan las marcas directas
para corroborar las fases decisivas.

Los APK, logs, catálogos, fotos y trazas permanecen privados bajo
`dist/analysis/gcam-preview-20261011/`. Corridas: `probe_plain_01`,
`probe_trace_01`, `probe_v2_plain_01`, `probe_v2_trace_01` y `original_trace_02`.
La corrida V2 con ftrace tiene sus logs en `measurements/measurements/` y su
traza en `measurements/`, debido al argumento de salida empleado; los artefactos
se conservaron para permitir reproducir el análisis.

Herramientas nuevas: `prepare_preview_probe.py`, `StartupTimeline.smali`,
`collect_preview_trace.py`, `summarize_preview_probe.py` y
`analyze_preview_trace.py`. El repacker admite sustituir también el DEX principal
y verifica integridad DEX y que todas las otras entradas ZIP sigan intactas.

## Próxima modificación respaldada por este análisis

Priorizar la reutilización de consultas de perfiles por cámara/calidad y la
preparación anticipada del resultado de `hir.J`, fuera del hilo principal, con
publicación sincronizada. El Map actual no es seguro para invocaciones concurrentes:
añadir un hilo sin controlar ownership, cache y ciclo de vida puede introducir
carreras. Tampoco basta con poner un worker y hacer `get()` bloqueante desde UI.
La dependencia PHOTO usa el resultado `isr.a`; debe verificarse qué parte de la
matriz es indispensable antes de aplazar las listas restantes hasta modo vídeo.

Después, abordar el escaneo masivo y el trabajo redundante de OptionsBar. Las
operaciones sobre Views y callbacks de UI deben permanecer en el hilo principal.
El ahorro real deberá medirse con aperturas A/B intercaladas y validación de las
tres cámaras, cambio a vídeo y primera captura. Los tiempos de bloques anidados
no se suman para prometer un ahorro.

Esta priorización coincide con la documentación oficial de Android sobre
[análisis de arranque](https://developer.android.com/topic/performance/appstartup/analysis-optimization)
y [TTID frente a apertura completa](https://developer.android.com/topic/performance/issues/launch-time).
La API consultada está documentada en
[CamcorderProfile](https://developer.android.com/reference/android/media/CamcorderProfile).
La identificación de `IC.hideRequestFromApi` se verificó en el
[código de ImeInsetsSourceConsumer](https://android.googlesource.com/platform/frameworks/base/+/refs/heads/main/core/java/android/view/ImeInsetsSourceConsumer.java).

## Estado final

Se restauró el APK original, sin montajes de ensayo, y ART `speed-profile` dio
`Success`. SHA-256 original:
`132e18273b3aafdb93e851f5db88156bd4f82c5032ad8de6594fa5a49ea6fe89`.
No se modificaron los módulos RAW/APatch. Esta entrega es diagnóstico; los APK
instrumentados no se ofrecen como optimizaciones finales.
Se retiraron los dos APK de ensayo del dispositivo y se verificó trazado apagado
y flags de atrace restaurados a cero. Una captura posterior con el APK original
produjo un JPEG de 3000×4000, decodificado e inspeccionado visualmente. Esto
comprueba la captura principal, no constituye una nueva validación completa de
RAW, las tres cámaras o la calidad fotográfica comparativa.
Las herramientas Python pasan `py_compile`; la comprobación de higiene del
repositorio y de sus dos módulos dio `PASS`.
