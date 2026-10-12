# Cuaderno de laboratorio: análisis y optimización del arranque de BSG GCam

**Fecha de consolidación:** 12 de octubre de 2026  
**Dispositivo:** Infinix Zero X Neo X6810-GL, Android 16 GSI, root APatch  
**Paquete:** `com.android.MGC_9_7_047`, BSG GCam 9.7.047 V32  
**Versión vigente al redactar:** módulo separado `x6810_gcam_startup` 0.5.0  
**Restricciones de laboratorio:** ADB directo; ARTEMIS no se usa. La 0.5.0 quedó activa en `modules_update`; no se reinició para esta activación.

Este cuaderno reúne el recorrido técnico, las decisiones y las mediciones de
los informes particulares enlazados al final. Conserva la distinción entre un
error reproducible, una hipótesis, una mejora de una métrica y una mejora de la
experiencia de abrir y tomar una foto. Los artefactos de dispositivo se generaron bajo `dist/analysis/` y se excluyeron
de Git. El conjunto privado se eliminó en la limpieza de espacio de octubre de
2026; este cuaderno conserva los resultados resumidos y las herramientas.

## Resumen ejecutivo

La demora inicial no tuvo una sola causa. Se encontraron tareas redundantes de
Java/UI y dos defectos independientes: la aplicación reextraía una biblioteca
ELF de unos 39 MB porque comparaba CRC de representaciones distintas, y el
wrapper nativo de segmentación enviaba un directorio donde su motor esperaba un
archivo de caché. También había preparación de pestañas y suscripciones
puramente visuales del panel PHOTO antes de que el usuario lo abriera.

Las mejoras conservadas se integraron en cuatro etapas:

| Etapa | Cambio conservado | Evidencia principal |
|---|---|---|
| 0.2.0 | Caché temporal de consultas de perfiles, scan de cámaras limitado a IDs 0–5, filas PHOTO a demanda y ART `speed` | La combinación scan6 + caché adelantó la preview ~600 ms y el disparador ~637 ms en un ABBA de cuatro muestras por variante. |
| 0.3.0 | CRC que valida la representación ELF ya transformada sin descomprimirla y escribirla de nuevo | En diez aperturas por variante, mediana TTID 1584,5 → 1429,5 ms; cero reescrituras frente a diez. |
| 0.4.0 | Un cambio de cuatro bytes en el wrapper nativo para pasar el nombre del archivo de caché correcto | `initSegmenter` 4109 → 776 ms con caché válida; el error desapareció. El segmentador comienza después del preview/obturador y no se atribuye ese ahorro al inicio. |
| 0.5.0 | Diferir el enlace de suscripciones visuales y construir las pestañas del panel PHOTO al primer uso | Enlace de UI, mediana 387,636 → 337,685 ms. Disponibilidad conjunta de preview y disparador, mediana 2468,655 → 2449,454 ms en seis aperturas por variante. |

La última media de disponibilidad conjunta fue **2,530 → 2,441 s**, una
diferencia de 89 ms (3,5 %) en esa muestra. Su mediana mejoró 19 ms (0,8 %).
No se deben sumar los ahorros de las distintas etapas: usan bases, instrumentación,
métricas y condiciones distintas. No se ha demostrado una mejora de calidad
fotográfica ni se ha implementado un planificador general de modelos ML y
microvideo. En dos perfiles instrumentados, los factories identificados de
microvideo y la entrada JNI del segmentador empezaron después de que preview y
obturador estuvieran listos.

## Laboratorio reproducible

### Hardware y estado inicial

El trabajo se hizo sobre el X6810-GL conectado por USB, con depuración ADB
autorizada y el teléfono desbloqueado durante UIAutomator, capturas y pruebas de
panel. El serial utilizado en la tanda final fue `07264251AK002755`; confirmar
el serial actual en cada sesión y sustituirlo en los comandos. No se usó
ARTEMIS. Root APatch se utilizó para los montajes temporales y el módulo
independiente de GCam; el módulo RAW del proyecto se mantuvo separado.

Estado de cámara documentado para el teléfono: S5KGM1ST principal de 12 MP,
OV08A10 telefoto de 8 MP con OIS y HI1631Q frontal de 4 MP. RAW/Camera2 Level 3,
control del brillo de flash SINGLE y TORCH, Android 16 GSI. Estas funciones son
parte del estado de partida; los parches de arranque descritos aquí no cambian
el HAL, los sensores, los buffers RAW, la exposición ni los parámetros de
procesamiento.

El APK base extraído del dispositivo y aportado al proyecto tiene SHA-256
`132e18273b3aafdb93e851f5db88156bd4f82c5032ad8de6594fa5a49ea6fe89`, tamaño
457584902 bytes, paquete `com.android.MGC_9_7_047`, versión
`9.7.047.702121536.18`. El APK base y su árbol decompilado eran privados y no se incluyen en el repositorio;
la copia de análisis local se eliminó en octubre de 2026. El payload modificado
actual se conserva por separado en `gcam/apatch-startup/payload/`.

### Herramientas y preparación del host

Se requiere Windows/PowerShell en la ruta usada para reproducir los comandos,
Python, Java, Android Platform Tools (`adb`) y el `apktool.jar` ya disponible en
`C:/Windows/apktool.jar`. Las pruebas DEX usan la clase local
`gcam/apk-analysis/AssembleSmali.java`, que ensambla DEX 039/API 28 con la
versión de smali incluida en apktool. No se debe sustituir por un ensamblador
que emita DEX 041 con cabecera clásica: ART rechazó esa combinación en una
prueba temprana.

Antes de una sesión:

```powershell
adb devices -l
adb -s SERIAL get-state
adb -s SERIAL shell getprop ro.product.device
adb -s SERIAL shell getprop ro.build.version.release
adb -s SERIAL shell pm path com.android.MGC_9_7_047
adb -s SERIAL shell dumpsys media.camera
```

Comprobar que existe un solo teléfono de destino, está en estado `device`, es
el X6810 y que el paquete señala un único `base.apk`. No cambiar de APK GCam,
ROM, firmware ni configuración entre las variantes de una comparación. Conservar
la configuración fotográfica del usuario; la preferencia `device_key`, el modo
microvideo y `avc_profile_high_supported` no se alteraron en las correcciones
retenidas.

La extracción usada para la auditoría completa incluye Manifest, recursos y
smali de los tres DEX. JADX 1.5.6 se usó en el análisis inicial y produjo 16150
archivos Java con 2220 errores; ese árbol duplicado se eliminó después. El
índice completo
conservado tiene 17188 clases, 107683 métodos definidos, 457957 instrucciones
invoke y 401925 referencias a campos. El índice es sintáctico; reflexión, JNI,
interfaces y código nativo requieren análisis aparte.

Para volver a generar el árbol principal desde el APK instalado, usar la ruta
que devuelve el propio Package Manager, no una ruta copiada de otra instalación:

```powershell
adb -s SERIAL shell pm path com.android.MGC_9_7_047
adb -s SERIAL pull /data/app/RUTA-DEVUELTA/base.apk dist/analysis/NUEVO/apk/base.apk
java -jar C:/Windows/apktool.jar d -f dist/analysis/NUEVO/apk/base.apk -o dist/analysis/NUEVO/apktool
Get-FileHash dist/analysis/NUEVO/apk/base.apk -Algorithm SHA256
```

El path de `adb pull` del ejemplo debe reemplazarse con la ruta exacta impresa
por `pm path`; `NUEVO` también debe ser una etiqueta nueva. Guardar el log de
apktool, el hash, el Manifest y el número de DEX junto a la extracción. El
smali/DEX es la referencia ejecutable; modificar solo una copia aislada.

### Método de medición

Las comparaciones de proceso frío usan `am force-stop`, pausa corta y `am start
-W`, manteniendo datos y cachés de archivos. No equivalen a borrar datos, vaciar
la caché de páginas ni arrancar justo después de reiniciar. Los benchmarks no
capturan screenshots durante la ventana de medida. Cuando corresponde, se usa
secuencia A/B/B/A, un calentamiento por bloque excluido y se guardan todos los
resultados originales, incluidos fallos y muestras lentas.

Se registran métricas distintas: TTID (`am start -W`), `onCreate`, recepción de
frame, render de preview, disparador habilitado y estado estable. Las marcas
desde el host incluyen overhead de ADB; los spans internos están anidados. No
sumar spans anidados ni tratar `ModeSwitcher WAS ALREADY ENABLED!` como prueba
de preview funcional, TTFD o capacidad de guardar una foto. Para aproximar
funcionamiento se usa una sonda de captura con botón localizado por la jerarquía
UI y se comprueba el JPEG final decodificable, dejando claro que el tiempo de
archivo incluye cola del input, procesado y escritura.

No se fijaron frecuencia DVFS, temperatura de cada corrida, procesos externos
ni estado de caché del filesystem. Las muestras son pequeñas y no respaldan una
prueba de significancia estadística. El arranque inmediatamente posterior a
reinicio se trata por separado, porque puede coincidir con montaje y compilación
ART.

### Montaje reversible de una variante APK

Los APK reconstruidos no conservan una firma que permita instalar una
actualización normal. El laboratorio los prueba montando temporalmente el
payload sobre el APK ya instalado con APatch. No se desinstala GCam, no se
deshabilita la verificación de firmas y no se escribe sobre el APK original.
Los runners guardan hashes y restauran el montaje en `finally`; aun así, antes
de cambiar de variante se debe comprobar el estado del montaje y el resultado
de compilación ART.

Ejemplo de prueba controlada con una herramienta que valida el hash:

```powershell
python gcam/apk-analysis/mount_trial.py --serial SERIAL apply --apk RUTA_APK --expected-trial-hash HASH
adb -s SERIAL shell cmd package compile -m speed -f com.android.MGC_9_7_047
adb -s SERIAL shell am force-stop com.android.MGC_9_7_047
adb -s SERIAL shell monkey -p com.android.MGC_9_7_047 1
python gcam/apk-analysis/mount_trial.py --serial SERIAL restore --expected-trial-hash HASH
```

Usar el componente/launcher que indique `monkey` o el Manifest si difiere en
esa build; las actividades internas no exportadas pueden rechazar el `am start`
directo. Para la variante nativa existe `mount_native_trial.py`. Para pruebas
combinadas deben restaurarse ambos montajes. No ejecutar dos runners sobre el
mismo teléfono a la vez.

En el módulo APatch vigente la instalación se hizo con:

```powershell
python gcam/apatch-startup/build.py gcam/apatch-startup/payload/x6810-gcam-startup-0.5.0.apk dist/x6810-gcam-startup-0.5.0.zip --native gcam/apatch-startup/payload/libgcastartup-cache.so
adb -s SERIAL push dist/x6810-gcam-startup-0.5.0.zip /data/local/tmp/x6810-gcam-startup-0.5.0.zip
adb -s SERIAL shell su -M -c '/data/adb/ap/bin/apd module install /data/local/tmp/x6810-gcam-startup-0.5.0.zip'
adb -s SERIAL shell su -M -c '/system/bin/sh /data/adb/modules_update/x6810_gcam_startup/activate.sh apply'
adb -s SERIAL shell su -M -c '/system/bin/sh /data/adb/modules_update/x6810_gcam_startup/activate.sh status'
```

Se restaura el APK/nativo mediante `activate.sh restore` de la misma versión.
Antes de sustituir payloads montados, primero restaurar la versión actualmente
activa. El módulo valida dispositivo, hashes, ruta instalada y propietario de
los dos montajes; compila con ART `speed` y revierte montajes nuevos si falla.
La 0.5.0 está en `/data/adb/modules_update/x6810_gcam_startup`; su promoción a
`modules` y su activación automática después de reiniciar no se verificaron en
esta etapa. El procedimiento de restauración está en
[`gcam/apatch-startup/README.md`](../gcam/apatch-startup/README.md).

## Cómo se detectaron los cuellos de botella

### Primeros registros y descarte de causas HAL

La investigación de septiembre comparó aperturas de GCam con la cámara nativa
Transsion y conservó logcat, `am start -W`, dumps de cámara y trazas. Se corrigió
la estimación inicial del usuario de diez segundos a una demora habitual
percibida de 5–6 s. Una apertura fría de proceso con el sistema ya iniciado
mostró TTID de 1,76–2,32 s; el primer inicio después de reiniciar llegó a
5,19 s y aún mostraba pantalla negra en una captura solicitada a 6 s. La cámara
nativa obtuvo TTID de 0,76–1,23 s, pero no se compararon funciones equivalentes.

`configureStreams_3_6` tardó 29–57 ms en varias aperturas; los bloqueos de UI
continuaban después de configurar streams. Por eso no se parchearon policy,
drivers, buffers RAW, sensores ni puentes de OIS/flash para explicar esos
segundos. Una traza temprana mostró trabajo de `bindApplication`, inicialización
del controlador e `UiWirer#wire`, además de competencia por CPU. Los intervalos
se solapan y no se suman. Otro muestreo ubicó una pila en
`LayoutInflater → Typeface.create → FontController/AssetManager`, evidencia de
un posible foco de trabajo, no prueba de que las fuentes expliquen todo el
arranque.

`atrace` no pudo escribir `record-tgid`; Perfetto reinició `traced` en un intento.
Se recuperó ftrace directamente con root y se importó con Perfetto v58.2. Algunas
trazas informan errores de parsing del vendor (259–288 en ensayos distintos),
por lo que se usaron para localizar tareas y dependencias, no como cronómetro
perfecto. Se observaron frames del sensor antes de terminar controlador/UI y
logs de TensorFlow Lite/OpenCL y encoders, sin concluir por ello que esos
componentes retrasaran la preview.

### Auditoría estática del APK

Se extrajo el APK activo con `pm path`/ADB y se decodificó con apktool y JADX.
Se cruzaron rutas Java con smali y un inventario SQLite de invocaciones/campos.
La revisión siguió `Application`, providers, `CameraApp`, apertura Camera2,
creación de controlador, montaje de Views, `nsu.a()`/`leb`, caches, JNI, ELF,
`MediaCodec`, hilos y dependencias de modos. No se asumió que el código Java
descompilado por JADX fuera recompilable ni que un string de log identificara
por sí solo un estado real.

Así se identificaron, en orden práctico, el barrido de 250 IDs pese a que el
X6810 publica los IDs 0–5; consultas repetidas al construir las seis listas de
perfiles PHOTO; filas del panel creadas al primer uso; extracción CRC de una
biblioteca oculta; discrepancia archivo/directorio en la caché del segmentador;
y tiempo de `UiWirer`. La selección final se hizo con pruebas A/B, no solo por
la presencia de código potencialmente caro.

### Error CRC: de log y mtime a defecto verificable

`com.android.app.Application.b()` extrae
`assets/QrQJbYT787QDr7Co` como `cache/codec_hevc.lck`, cambia los primeros tres
bytes para reconstruir la cabecera ELF y luego lo carga con `System.load`.
El asset enmascarado mide 38953640 bytes y su CRC es `a6628e96`; la copia ELF
transformada conserva el tamaño, pero tiene CRC `4502f6fb`. El verificador
comparaba el CRC de la copia transformada con el del asset enmascarado, por lo
que consideraba inválida una copia correcta y volvía a descomprimir/escribir
unos 39 MB en cada apertura. El cambio de mtime y la igualdad del resto de bytes
se verificaron extrayendo la copia por ADB.

### Caché de segmentación: error del SO y caller JNI

Primero se vio `Unable to open file for writing: Is a directory` y
`Could not initialize inference engine`. Una instancia aislada de ftrace
confirmó `openat` con `EISDIR` en `GcaGeneric-1`, sin pila de usuario útil.
Inspeccionar sólo el log no permitió decidir cuál API recibía ruta de archivo o
directorio: otras rutas de segmentación sí agregan nombres de archivo al
directorio. Se siguió el argumento desde `lqv.b()` hasta el JNI y se desensambló
el wrapper AArch64. Así se aisló el llamador exacto que aplicaba `dirname` al
nombre completo antes de pasarlo como archivo al motor.

Una primera sonda Frida para I/O provocó SIGSEGV y no generó evidencia válida;
se retiró. Otra observación Frida había alterado/bloqueado la inicialización.
La conclusión se basó en llamada JNI, ruta registrada, offset/bytes del ELF y
comparación reversible con la biblioteca original, no en esos hooks fallidos.

### Panel y suscripciones: medidas y análisis de consumidores

Las trazas situaron `cameraUiModule#inflate` entre ~334–460 ms,
`UiWirer#wire` entre ~308–516 ms y `OptionsBarCtrl#wireAutobahn` entre ~146–176 ms
en aperturas distintas. No son aditivos. Se siguió `nsu.a()` y los consumidores
de campos de `leb`: algunos coordinan cámara, gestos, ciclo de vida y minibar,
pero el recorrido de `jyh` caso 13 acaba actualizando sólo la vista de opciones.
El recorrido caso 14 tiene efectos de estado/cámara y permanece eager.

La región original de TabLayout/ViewPager se extrajo según CFG con sus 534
líneas de instrucciones/etiquetas preservadas. Se añadió `PanelTabs.build(leb)`
y un helper de preparación en el hilo principal. Al primer uso se reproducen
las suscripciones visuales con valores actuales y se crean las pestañas; al
cerrar el panel se libera el estado pendiente. Se conservaron inflación de
contenedores, BottomSheetBehavior, gestos, ciclo de vida y estado de cámara
porque hay consumidores antes del primer uso. No se trasladaron operaciones de
View a un worker.

## Cambios exactos conservados por versión

### 0.2.0: búsquedas repetidas, IDs y filas de opciones

1. **Scan de cámaras:** `CameraLensesScan.scanCameraLens()` reduce el límite
   numérico 250 a 6, consultando IDs 0–5. Se contrastó con `dumpsys media.camera`
   en el X6810. Es específico de este HAL, no una regla para otros teléfonos.
2. **Perfiles:** un `ThreadLocal` limitado a una invocación de `hir.J(pui)` guarda
   resultados de `CamcorderProfile.hasProfile` por calidad, incluidos negativos,
   y `osh.aW` por objeto `pgf`. El wrapper conserva el cuerpo original, limpia
   la caché al retornar o al propagarse una excepción y no modifica el mapa
   persistente. Se evita repetir hasta 78 consultas a nueve calidades al crear
   seis listas. El orden, filtros y opciones originales se conservan.
3. **Filas:** en `kzh.run`, PHOTO con panel cerrado actualiza estado y guarda los
   cambios pendientes; la primera apertura o expansión llama al camino original
   para construir/actualizar las filas antes de mostrarlas. Otros modos siguen
   eager. Las vistas y callbacks siguen en main.
4. **ART:** el módulo valida y solicita compilación `speed`; no equivale a crear
   un Baseline Profile ni a mover trabajo fuera del hilo principal.

Prueba de caché de perfiles sola (seis muestras/variante): el controlador bajó
1074,4 → 866,7 ms; preview −156 ms y disparador −146 ms; TTID subió 22 ms. La
combinación de caché + scan6 (cuatro muestras/variante): TTID 1696 → 1297,5 ms,
preview −599,6 ms, disparador −637,3 ms. La primera captura fría enviada a
~3 s produjo JPEG a 7,70 s en original y 7,60 s con scan6, una sola captura por
variante: no demuestra una mejora de captura. Ver
[`PROFILE_RESULTS_20261011.md`](../gcam/apk-analysis/PROFILE_RESULTS_20261011.md).

### 0.3.0: evitar escritura repetida del ELF

Se modifica únicamente la primera llamada `bc(File)` en
`com.android.app.Application.b()` para invocar `x6810ElfAssetCrc(File, ZipEntry)`.
El helper comprueba tamaño y cabecera ELF, calcula CRC como si los tres bytes
transformados siguieran en cero, procesa el cuarto byte `46` y el resto en
bloques de 8192 bytes. Mantiene la validación de contenido; no sustituye CRC
por `exists()`, no omite lectura, no toca la segunda extracción ni altera
`System.load`. En cabecera/tamaño/error inválidos retorna −1, forzando el camino
original de extracción y recuperación.

En A/B/B/A con diez aperturas por variante, TTID mediana fue 1584,5 → 1429,5 ms;
preview −212 ms y botón −163 ms desde la marca ADB. El archivo se reescribió
10/10 veces antes y 0/10 después. La evidencia causal más fuerte es eliminar la
escritura repetida; los cambios de latencia son de esa muestra y el trabajo de
validación aún lee 39 MB. Se probaron copia válida, ausente, cabecera dañada,
contenido alterado, truncamiento y reutilización posterior; todo terminó con
SHA correcto. Informe: [`GCAM_CRC_FIX_20261011.md`](GCAM_CRC_FIX_20261011.md).

### 0.4.0: corregir el parámetro nativo de caché

En `libgcastartup.so`, dirección de archivo auditado `0x4618e68`, se reemplaza
la instrucción `BL dirname` (`1d126494`) por NOP (`1f2003d5`). El wrapper
conserva x0/x1 con el nombre de archivo que el caller ya había construido; no
se cambia el `dirname` común ni los demás consumidores. El ELF conserva tamaño,
se verifica SHA original antes de parchear y cambia una sola instrucción.
La compilación de modelos, precisión, delegado, mutex, escritura de caché y
fallback mantienen el flujo original.

ABBA con cuatro muestras por variante: `initSegmenter` bajó de 4109,066 a
776,190 ms (−81,1 %) con una caché válida. Caché ausente tardó ~4265 ms la
primera vez; truncada, ~4255 ms; ambas se regeneraron y las reaperturas quedaron
en ~685–808 ms. El error estuvo en 4/4 muestras originales y 0/4 corregidas.
Como la entrada ocurrió después de preview y disparador, no se afirma que la
reducción de 3,33 s acelere el primer encuadre. Informe:
[`GCAM_SEGMENTER_CACHE_FIX_20261011.md`](GCAM_SEGMENTER_CACHE_FIX_20261011.md).

### 0.5.0: pestañas y suscripciones del panel PHOTO

En `nsu.a()`, el caso 13 del recorrido `jyh` guarda la suscripción puramente
visual en la instancia de `leb`, en vez de invocar inmediatamente
`OptionsMenuView.A(category, value)`. El caso 14 que llama a `ler.m(leb)` queda
intacto para mantener estado/cámara/minibar. El bloque original de configuración
de tabs pasa a `x6810/gcam/PanelTabs.smali`; en PHOTO cerrado se llama al helper
de preparación al abrir por toque/gesto y antes de mostrar filas. Las
suscripciones leen el valor actual y se enlazan al `pdf` de ciclo de vida
original. Se conserva la creación inicial de estructura/gestos; se difiere lo
que no tiene consumidores hasta abrir.

El APK de módulo tiene SHA-256
`2218c653d91482b377877014bbc22610cb386c30465c4b831c944299f0ea1b83`; la
biblioteca nativa es idéntica a la 0.4.0, hash
`64cfcb3f598cdf3e75875bdd4cb8e8775a6763be15c3d2240d1d7ee0656f053a`. El ZIP
APatch 0.5.0 tiene SHA-256
`973bdc375f1d1c4d78b9a9cfbe7bfcb35300a54e68a5c24a45d2ed08286e239f`.
Sólo cambian las clases DEX necesarias; CRC del main DEX y parche nativo
anteriores permanecen.

ABBA con seis aperturas medidas por variante, filesystem caliente, sin
screenshot durante el inicio:

| Mediana | Control 0.4.0 | Panel 0.5.0 | Diferencia |
|---|---:|---:|---:|
| Enlace UI | 387,636 ms | 337,685 ms | −49,951 ms (12,9 %) |
| Controlador | 698,924 ms | 647,476 ms | −51,448 ms |
| TTID | 1446,5 ms | 1426 ms | −20,5 ms |
| Preview renderizada desde marca ADB | 2468,655 ms | 2434,549 ms | −34,106 ms |
| Disparador habilitado desde marca ADB | 2407,417 ms | 2312,845 ms | −94,572 ms |
| Preview y disparador listos (máximo de ambos) | 2468,655 ms | 2449,454 ms | −19,201 ms |

El promedio conjunto fue 2530,111 → 2441,178 ms (−88,933 ms). La mediana es
menos favorable y los grupos de esta métrica se solapan. No se afirma un ahorro
universal de 89 ms ni significancia estadística. Al primer toque, preparar tabs
tardó 41,444 ms y el helper 42,577 ms; la segunda apertura reutiliza esas tabs.
La verificación funcional de la release cubrió toque/gesto, General/Pro,
Google AWB, cámara frontal, principal, telefoto 4.9, Retrato/PHOTO y HOME/
reanudación. Las jerarquías mantuvieron las opciones y textos del control.

Después se activó la versión en el dispositivo y se tomaron/decodificaron JPEG:
principal 3000×4000, frontal 1744×2320 y telefoto 2448×3264. La cámara se dejó
en PHOTO, principal 1.0. Una apertura fría aislada reportó TTID 2044 ms; no es
promedio ni reemplaza ABBA. Los tiempos hasta que se observó cada archivo son
tiempos de captura/procesamiento, no una medida nueva de apertura. Informe:
[`GCAM_PANEL_OPTIMIZATION_20261011.md`](GCAM_PANEL_OPTIMIZATION_20261011.md).

## Cambios ensayados sin mejora clara o que se dejaron pendientes

| Ensayo/candidato | Qué se cambió o midió | Resultado y decisión |
|---|---|---|
| `ois_api_supported=false` | Preferencia temporal para silenciar la inconsistencia OIS | Desapareció `Null OIS keys`; TTID 1,55 s frente a 1,76 s de un control cercano, variación insuficiente; `OIS is dead` continuó. Se revirtió. |
| `camera.on_demand_ui_wirer` | Se alternó la preferencia | Controles sin ajuste 2,40/3,54 s y ajustado 2,38/2,57/2,81 s; sin ventaja estable. Además, el APK fija `true` por defecto salvo valor explícito. Revertido. |
| `device_key=redfin` frente a `raven` | Perfil alternativo del teléfono | Ambos quedaron en ~2,15–2,51 s; no mejoró y el usuario observó lo mismo. Restaurado `raven` en aquel ensayo. |
| ART `speed` frente a `speed-profile` | Forzar compilación | Primeras pantallas 2,46/2,74/2,17 s; rango normal solapado. No arregló el arranque en frío; `speed-profile` se restauró en ese ensayo. Las versiones posteriores del módulo sí validan ART `speed` como requisito de montaje. |
| `camera.prewarm_viewfinder_surfaceview=true` | Precalentar la superficie de viewfinder | TTID 2,22/2,07 s frente a 2,15/2,15 s; proxy de controles no mejoró. Revertido. |
| `gcam.zsl_buffer_size=3` | Reducir buffer ZSL desde 9 | TTID con 3: 2,23/2,17 s; con 9: 2,10/2,02 s. Controles también fueron algo más lentos con 3. Se restauró 9. |
| Parche `nolog` / logging BSG | Hook que hace retornar `StartLogging` | En ensayos tempranos nolog tuvo TTID mediano 1758 ms y proxy 2926 ms, sin ventaja. La preferencia separada `pref_disable_log_key=1` sí quitó el proceso de captura logcat y redujo TTID 1625 → 1508 ms en ABBA de seis muestras, pero el disparador sólo mejoró 17 ms. Se mantuvo como preferencia reversible del usuario, no como parche APK ni como promesa de cámara lista. |
| Precarga de 46 clases en worker | `Class.forName(..., false, loader)` en worker de baja prioridad | En seis muestras frente a control reconstruido: TTID −107,5 ms y proxy −223,5 ms; rangos solapados, el worker medido duraba 0–1 ms y control difería del original. Señal modesta sin atribución causal; no integrada. |
| Precarga de tres Google Sans | Añadida al mismo worker de clases | Mediciones válidas: TTID mediana 1897 ms, proxy 3213,5 ms, peores que el control; dispersión grande. No se infiere que las fuentes causen regresión, pero no hay beneficio. |
| `CamcorderProfile.hasProfile(0,0)` en worker | Inicialización pequeña del framework de perfiles | TTID 1193,5 → 1218,5 ms (peor 25); preview −28,5 ms; disparador +8,7 ms; steady +100,9 ms. Rangos preview muy solapados; worker descartado. |
| Mover inicialización completa de UI/controlador a workers | Análisis de `jpp`/`jnr`, `pdh`, `jmt`, Camera2 y Views | No se ejecutó como parche general: métodos mezclan Views, Choreographer, estado mutable, callbacks y dependencias de cámara. Android exige afinidad UI. La solución aplicada difiere trabajo secundario y conserva la construcción necesaria en main. |
| Inflar el panel entero en background | Propuesta inicial | No se aplicó: `nsu.a()` es main-thread y crea/referencia estructura, gestos, ciclo de vida y cámara. No se demostraron los requisitos de LayoutParams/Looper de toda la jerarquía. Se aplazaron sólo tabs y suscripciones visuales seguras. |
| Diferir más los factories `qiv` / segmentador | Sonda en dos aperturas principales | `qiv` comenzó a 2025/2427 ms; JNI de segmentación a 2415/2307 ms; para entonces preview y disparador estaban disponibles a 1822/1920 ms. Un retraso adicional no demuestra ahorro en la apertura. No integrado. |
| Cambiar encoder de vídeo a HEVC o acelerador distinto | Propuesta por presencia de MediaCodec, Mali/OpenCL, NNAPI/APU en sistema | No se modificó: el panel y la carga Java dominaban parte del camino; `jbe.f()` depende de EGL actual; soporte de NNAPI/operadores para esos modelos no se comprobó. El cambio puede afectar compatibilidad, Top Shot, audio o calidad; no hay comparación positiva. |
| Reemplazar globalmente rutas de caché similares | Primera lectura del error EISDIR | Descartado al encontrar callers con contratos diferentes: algunos esperan archivo y otros directorio. Sólo se parcheó el caller JNI demostrado. |
| Hooks Frida de caché | Instrumentación dinámica de I/O/JNI | Un intento terminó en SIGSEGV y otro alteró/bloqueó la llamada. No es evidencia válida de rendimiento; se retiró el servidor y no se retuvo el hook. |
| Inicio inmediatamente tras reboot | Montaje y compilación ART `speed` concurrieron con primer lanzamiento | Una primera presentación observada tardó 6668 ms y había controles sobre preview negra a la captura solicitada a 8 s; HAL configuró en 89 ms. No es un A/B limpio ni se puede atribuir todo a ART. El objetivo específico de primera apertura tras reinicio continúa abierto. |

La cámara nativa Transsion sirve como referencia, no como candidato de
configuración transplantable. No se activaron NNAPI, Hexagon, GXP, EdgeTPU ni
un encoder “más rápido” por encontrar esos nombres en strings o librerías. Que
un codec sea hardware no implica que acelere TTID, Views, apertura Camera2 o el
pipeline RAW. Toda optimización de competencia debe medirse contra la captura
inmediata, Top Shot/Motion Photo, audio y transición de modos.

## Resultado actual y límites

La secuencia de lanzamientos medidos mejora rutas concretas y elimina dos
fallos comprobados. No existe una única comparación original-vs-0.5.0 de todas
las versiones bajo un mismo A/B/B/A; por eso no se publica un porcentaje total
acumulado. La última comparación controlada evalúa solamente panel 0.5.0 frente
a su control 0.4.0. La experiencia reportada de 5–6 s incluía escenarios más
lentos, inicio tras reinicio y métodos de observación distintos; no debe
compararse directamente con el promedio de proceso frío de 2,44 s.

Las capturas finales demuestran que los tres sensores guardan archivos JPEG
decodificables con el módulo actual. No son una prueba ciega de nitidez,
exposición, color, latencia RAW, OIS ni reducción de ruido. La foto telefoto de
la prueba anterior estaba desenfocada en una escena cercana. No se repitió en
0.5.0 la matriz completa de DNG, flash SINGLE/TORCH, vídeo largo, Top Shot y
estabilidad térmica; esos componentes no fueron modificados.

La primera apertura del panel sí paga parte del trabajo aplazado: el helper de
preparación midió 42,577 ms en una muestra instrumental. La sonda no ejecutó una
acción de accesibilidad dedicada; se verificó gesto y se conservó el callback
de expansión. La persistencia de activación de 0.5.0 a través de reinicio sigue
pendiente porque el usuario pidió no reiniciar.

## Evidencia y reconstrucción

Las capturas, preferencias privadas, APK extraído, árboles decompilados,
índices, trazas, logs y resultados crudos se guardaron en `dist/analysis/`, una
carpeta local ignorada por Git. Todo ese conjunto se eliminó en la limpieza de
espacio de octubre de 2026. Este cuaderno conserva los hallazgos y las métricas
resumidas, pero los archivos fuente de aquellas mediciones ya no están en este
checkout. Repetir los análisis que dependían del APK instalado requiere volver
a extraer una copia compatible del teléfono; las mediciones de rendimiento
requieren nuevas capturas en el dispositivo.

Los scripts de investigación se mantienen en `gcam/apk-analysis/`. Los
paquetes actuales no dependen de los datos eliminados: sus módulos completos
están en `modules/` y los payloads versionados de GCam en
`gcam/apatch-startup/payload/`. Para generar la release recomendada desde el
repositorio:

```powershell
python scripts/package_github_release.py --raw-version v001 --output-dir dist/github-release
```

La limpieza retiró solo resultados locales; no cambió fuentes, módulos,
parches, manifiestos ni herramientas. `dist/` se vuelve a crear cuando se
construyen paquetes o se recogen nuevas mediciones.

## Informes relacionados

- [Estado vigente y mediciones históricas por versión](GCAM_STARTUP_CURRENT.md)
- [Auditoría completa de APK/DEX/ELF](GCAM_APK_FULL_AUDIT_20261011.md)
- [Pruebas sin resultados concluyentes de septiembre](GCAM_STARTUP.md)
- [Primer diagnóstico y trazas de octubre](GCAM_STARTUP_20261011.md)
- [Caché de perfiles y scan6](../gcam/apk-analysis/PROFILE_RESULTS_20261011.md)
- [Filas de opciones diferidas 0.2.0](../gcam/apk-analysis/LAZY_OPTIONS_RESULTS_20261011.md)
- [Ensayos de hilos](../gcam/apk-analysis/THREAD_RESULTS_20261011.md)
- [Precalentamiento de perfil en worker](../gcam/apk-analysis/PARALLEL_STARTUP_RESULTS_20261011.md)
- [Corrección del CRC ELF 0.3.0](GCAM_CRC_FIX_20261011.md)
- [Caché del segmentador 0.4.0](GCAM_SEGMENTER_CACHE_FIX_20261011.md)
- [Panel y diagnóstico de ML/microvideo 0.5.0](GCAM_PANEL_OPTIMIZATION_20261011.md)
- [Construcción y restauración del módulo APatch](../gcam/apatch-startup/README.md)
