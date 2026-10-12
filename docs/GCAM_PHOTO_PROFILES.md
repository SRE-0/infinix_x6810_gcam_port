# Perfiles fotográficos BSG V18 para X6810-GL

Investigación iniciada el 10 de octubre de 2026 mediante ADB y root APatch.
Los perfiles son **experimentales**: compatibilidad funcional y calidad
fotográfica son verificaciones distintas. No contienen calibraciones de fábrica
nuevas ni una mejora garantizada de los tres sensores.

## Compatibilidad e integración

El teléfono usa `com.android.MGC_9_7_047`, versión
`9.7.047.702121536.18`, con APK SHA-256
`132e18273b3aafdb93e851f5db88156bd4f82c5032ad8de6594fa5a49ea6fe89`.
Se extrajo ese APK del dispositivo para analizarlo. El APK que estaba guardado
en el diagnóstico anterior tenía un hash diferente; sus clases no se consideran
prueba de compatibilidad del APK instalado.

El módulo montado sigue siendo v001 `x6810_raw12mp`; se identificó también
`x6810_camera_ros` 0.3.0 experimental. No se reinstalaron módulos ni se modificaron
sus binarios. Los cambios fotográficos de este trabajo son preferencias de la
aplicación y parches que **la propia GCam** aplica en su proceso.

| Sensor | ID Camera2 | RAW publicado |
|---|---:|---:|
| S5KGM1ST | 0 | 4000×3000 |
| HI1631Q | 1 | 2320×1744 |
| OV08A10 | 2 | 3264×2448 |

Los perfiles se mantienen en [gcam-bsg-v18.json](../profiles/gcam-bsg-v18.json).
El aplicador [configure_mgc_photo.py](../scripts/configure_mgc_photo.py) comprueba
versión y hash del APK antes de escribir, detiene la aplicación, guarda un
respaldo privado, conserva el inode/permisos/contexto del XML y verifica su
lectura. Modifica las claves del perfil elegido; las variantes nocturnas incluyen
AWB de Night Sight y autofocus compartidos por las cámaras traseras. Si una escritura falla,
intenta restaurar el contenido inmediatamente anterior.

```powershell
python scripts/configure_mgc_photo.py status --serial SERIAL --backup-dir .local-private/photo-backup --sensor tele
python scripts/configure_mgc_photo.py apply --serial SERIAL --backup-dir .local-private/photo-backup --sensor tele
python scripts/configure_mgc_photo.py restore --serial SERIAL --backup-dir .local-private/photo-backup --sensor tele
```

El perfil `tele` estándar usa factores neutros. Para repetir el ensayo de
textura, añadir `--variant detail` a `apply`, `status` o `export` con `--sensor tele`.
Ese ensayo no se recomienda todavía como mejora demostrada. La frontal sigue
pendiente de validación fotográfica; sus valores son un candidato conservador.

`--sensor all` selecciona los tres sensores. `export` genera un XML completo a
partir de las preferencias actuales, con el overlay seleccionado. Es una copia
privada de ajustes de la aplicación, no un XML mínimo genérico ni un archivo
para otra revisión del port. Las exportaciones quedan en el directorio indicado
y no se distribuyen en el repositorio. La restauración solo devuelve las claves
del perfil; conserva otros ajustes realizados después del respaldo.

## Variante nocturna: principal y telefoto

`--sensor rear --variant night` selecciona exclusivamente S5KGM1ST (0) y
OV08A10 (2). La combinación nocturna rechaza `front` y `all`; no existe una
variante nocturna frontal. Para aplicarla y consultar sus valores:

```powershell
python scripts/configure_mgc_photo.py apply --serial SERIAL --backup-dir .local-private/night-backup --sensor rear --variant night
python scripts/configure_mgc_photo.py status --serial SERIAL --backup-dir .local-private/night-backup --sensor rear --variant night
python scripts/configure_mgc_photo.py export --serial SERIAL --backup-dir .local-private/night-backup --sensor rear --variant night
python scripts/configure_mgc_photo.py restore --serial SERIAL --backup-dir .local-private/night-backup --sensor rear --variant night
```

La aplicación queda detenida tras escribir: abrir GCam, seleccionar principal
o telefoto y **Night Sight**. Usar enfoque automático y sostener el teléfono
durante toda la integración. Los factores por sensor también se usan en otros
modos: V18 no proporciona aquí una tabla independiente de ruido para Night
Sight. Volver a `--variant standard` recupera el perfil diurno guardado en el
proyecto; `restore` recupera los valores anteriores al respaldo.

El XML de `export` incluye las preferencias actuales completas de GCam y
conserva las de la frontal. El overlay nocturno solo cambia claves traseras;
no es una configuración frontal nueva.

La variante `night` conserva los cuatro factores en 1,0, usa autofocus
(`pref_af_mode_back=0`) y AWB del sistema en Night Sight
(`pref_camera_gawb_b_ns=0`). `night-google-awb` conserva los mismos factores y
activa únicamente Google AWB nocturno (`pref_camera_gawb_b_ns=1`). Esta alternativa
enfría sombras y superficies plateadas en la iluminación mixta ensayada;
no equivale a una corrección de color calibrada. No cambia AWB del modo Foto
ni las claves AWB/foco de la frontal. En el telefoto, GCam normalizó el valor
guardado de foco a `1` al entrar en Night Sight; el menú seguía mostrando
autofocus seleccionado. La selección visible y el comportamiento prevalecen
sobre interpretar ese entero aisladamente.

La sesión terminó con **26 JPEG** conservados: nueve ensayos de factores y
cuatro comparaciones/verificaciones de AWB por cada sensor trasero. Las últimas
capturas de ambos sensores y sus lecturas nativas confirmaron factores neutros.
Se aplicó `night` mediante el aplicador público y se exportó un respaldo XML
privado. La aplicación quedó detenida para conservar la instantánea final.

Durante los cambios de modo, GCam vació su preferencia de resolución frontal;
se restauró al valor original `2320x1744` antes de cerrar la sesión. La comparación
final de 351 claves con sufijo `_1`, nombres frontales o AWB frontal no encontró
diferencias. No hubo capturas ni perfiles nocturnos de la frontal. No se cambiaron
los módulos APatch, bibliotecas vendor ni la calibración de fábrica.

Se ensayaron factores luma/chroma 1,125/1,25 y 0,875/1,125 frente al control
neutro, en tandas de tres fotografías por sensor. Los offsets y la selección
del modelo de ruido quedaron originales. La aplicación nativa de ambos pares
se verificó en la principal y del segundo par en el telefoto. La lectura del
primer par en el telefoto se hizo tras reiniciar la aplicación y no sirve para
confirmar aquel disparo.

En la principal, el control tuvo ISO 76–99 y 280–370 ms; el segundo candidato
abarcó ISO 98–2689 y 10–270 ms. Una toma del control estaba desenfocada y se
excluyó de la interpretación de textura. En el telefoto, los controles abarcaron
ISO 428–1273 y 40–450 ms. Estos son metadatos EXIF del JPEG, no la duración
completa ni la lista de exposiciones de la integración multiframe.

La comparación telefoto más cercana del primer candidato fue ISO 1273/1277,
40 ms: el gradiente de la zona de texto pasó de 0,03926 a 0,03863 y el gradiente
cromático de la pantalla oscura de 0,00190 a 0,00191. Una sola pareja, sin mejora
clara ni repetición equivalente, no justifica cambiar los factores. Se conserva
por ello una base nocturna neutra y reversible; no se anuncia una reducción de
ruido cuantificada ni mayor resolución. Los recortes y métricas de esta sesión
quedan privados junto a las fotografías.

## Ruta de procesamiento encontrada en V18

La clase `com.a` construye las claves por ID físico mediante
`VariableKeyLens`. El sufijo `_1` corresponde a la frontal, no a la principal.
Muchas preferencias antiguas del lib patcher estaban guardadas solo con ese
sufijo. La existencia de una clave o una pantalla no demuestra que su ajuste
modifique el procesamiento.

En el APK instalado, `RamPatcher.set_pthcr` pasa únicamente el mapa `dN` a
`setPathAll`. Ese mapa selecciona el modelo de ruido y cuatro instrucciones
de luma/chroma. `get_pthcr_addr` devuelve direcciones para esas cinco familias
y devuelve `null` para las familias habituales de sharpening, saturación,
gamma, factores de denoise y ganancia. Otras funciones con direcciones existen,
pero no se conectan a esta ruta del RAM patcher. Por ello no se han incluido
valores de `SharpenStrengthFactor`, `SharpTuning`, `Saturation`, ni curvas HDR
inventadas en los perfiles.

| Familia de clave (añadir `_ID`) | Offset en libgcastartup | Instrucción original |
|---|---:|---|
| `user_nm_pthcr_key` | `0x33277f8` | `ldrb w8, [x21, #0x70b]` |
| `LumaOffset_fmov_3f80_0000_pthcr_key` | `0x5f3645c` | `fmov s0, #1.0` |
| `LumaScale_fmov_3f80_0000_pthcr_key` | `0x5f365e8` | `fmov s1, #1.0` |
| `ChromaOffset_fmov_3f80_0000_pthcr_key` | `0x5f36b7c` | `fmov s1, #1.0` |
| `ChromaScale_fmov_3f80_0000_pthcr_key` | `0x5f37f8c` | `fmov s1, #1.0` |

Estas direcciones se verificaron contra la biblioteca del APK y mediante lectura
de `/proc/PID/mem` con root. Después de disparar con luma 0,875 y chroma 1,125,
se observaron respectivamente `01902d1e` y `01502e1e` en memoria; las instrucciones
neutrales eran `01102e1e`. Antes del primer disparo pueden seguir visibles los
valores originales. Restaurar y disparar devuelve los factores originales.
La selección del modelo de ruido quedó sin modificar.

Los nombres «Scale» y «Offset» no bastan para interpretarlos como multiplicadores
directos de cantidad de denoise: el ensamblador cercano contiene divisiones y
normalizaciones. La validación de sus efectos debe hacerse con fotografías.
Un cambio de instrucción demuestra aplicación funcional, no superioridad visual.

## HAL MediaTek y modelos de ruido

Se inspeccionaron los símbolos de `s5kgm1st_mipi_raw_tuning.so`,
`ov08a10_mipi_raw_tuning.so`, `hi1631q_mipi_raw_tuning.so` y
`libcam.hal3a.v3.dng.so`. Las bibliotecas de tuning publican
`RAWSensorInfo::impGetDefaultData`; el módulo DNG tiene
`DngInfoImp::getDynamicNoiseProfile` en `0x49e0`. Su ensamblador carga
coeficientes, combina multiplicaciones y sumas y limita resultados a valores
no negativos. Esto identifica una ruta de perfil dinámico, pero no acredita
una calibración correcta del sensor en todo el intervalo ISO.

Android define por canal CFA los coeficientes `S` y `O` con
`N(x) = sqrt(S*x + O)`, usando señal normalizada. Un DNG existente del dispositivo
incluía el tag `NoiseProfile`; esa muestra no se usa como calibración de ninguno
de los tres sensores sin comprobar su procedencia, ISO y plano RAW.
Referencia: [Camera2 SENSOR_NOISE_PROFILE](https://developer.android.com/reference/android/hardware/camera2/CaptureResult#SENSOR_NOISE_PROFILE).

Los archivos del Poco M3 y Samsung FE tienen esquemas de preferencias diferentes.
En el XML del Poco, los dieciséis campos de coeficientes de ruido encontrados
están vacíos; en el archivo AGC varios overrides están desactivados. Compartir
el nombre del sensor no justifica trasladar AWB, matrices, niveles negros,
ganancia o coeficientes de ruido entre módulos ópticos y firmwares.

Para construir un modelo físico hacen falta pares de RAW de campo uniforme y
oscuros a varios ISO, black/white levels, CFA y separación de ganancias analógica
y digital. Un JPEG de una escena natural no proporciona esos datos. No se han
fabricado coeficientes A/B/C/D ni modificado tablas ISP del firmware.

## Ensayos fotográficos y límites

Las capturas se hicieron mediante ADB con el disparador localizado en el XML
actual de UIAutomator. En Night Sight, la animación impidió obtener estado idle
en varias consultas: se usaron como respaldo sus límites de disparador
verificados visualmente a 1080×2460, con espera adicional entre capturas.
Se comprobó el ID activo en `dumpsys media.camera`,
aparición de un nuevo JPEG y estabilización de su tamaño antes de extraerlo.
Una apertura de GCam puede cambiar de lente durante la inicialización: el
nombre o la selección previa de la lente no reemplaza esta comprobación.

La principal tuvo doce capturas de control/candidato alternadas. La primera
tanda pasó de ISO 877 y 20 ms a ISO 680 y 30 ms. En una comparación cercana de
30 ms e ISO 663/676, el candidato aumentó los gradientes de madera, carcasa y
teclado alrededor de 6–7 %, pero otras zonas y disparos no reprodujeron ese
resultado. Es evidencia exploratoria; los gradientes también aumentan por
ruido, enfoque y sharpening. No equivale a una mejora de resolución del 7 %.

En el telefoto se verificó primero aplicación del factor chroma 1,125 y captura
JPEG de 2448×3264. La sesión exterior posterior permite comprobar textura de
tejas/ladrillos, blancos, sombras y objetos de color. Se compararon factores
neutrales, el candidato de chroma, enfoque infinito, Google AWB y HDR+ mejorado.
La exposición exterior rondó ISO 100 y 1,5–1,7 ms, con cambios de iluminación.

La sesión exterior terminó con 21 fotografías válidas en siete tandas de tres:
chroma 1,125, control neutro, infinito, Google AWB, HDR+ mejorado, ensayo de
textura y repetición de control HDR+ mejorado. El ensayo de textura usó luma
0,875/chroma 1,125. Sus exposiciones fueron 0,991–1,340 ms; los controles HDR+
mejorado abarcaron 1,622–2,060 ms. Las advertencias del analizador impiden
atribuir sus diferencias solo a los factores. Se conservó el perfil estándar
neutro y se guardó el ensayo como variante `detail`.

La mediana del clipping de al menos un canal en la ROI de pared iluminada fue
0,86 % con HDR+ normal, 0,14 % en el primer control HDR+ mejorado y 0 % en su
repetición. Esto describe estas muestras, sujetas a iluminación cambiante;
no prueba un incremento del rango dinámico físico del sensor. Google AWB
produjo un aspecto más frío en las paredes y se restauró a desactivado.

Fijar enfoque infinito (`pref_af_mode_back=4`) empeoró claramente las tejas y
ladrillos frente al autofocus (`0`); se descartó. Google AWB se controla con
`pref_camera_gawb_b_photo` (0/1), y HDR+ mejorado con
`pref_camera_hdr_plus_key=on` frente a `auto` para HDR+ normal. Estos ajustes
son compartidos por la aplicación para captura; no son overrides exclusivos
del sensor 2. El perfil no los escribe de forma implícita.

Las comparaciones de color no usan carta calibrada: las paredes pueden tener
color propio y las sombras reciben luz distinta. La evaluación de altas luces
mide clipping del JPEG, no rango dinámico RAW en pasos. Una sesión exterior a
ISO 100 tampoco valida reducción de ruido nocturna o de alto ISO.

El analizador [analyze_mgc_photos.py](../scripts/analyze_mgc_photos.py) genera
EXIF, métricas por ROI y advertencias cuando ISO/exposición varían más del 10 %.
También informa intervalos dentro de cada tanda. No alinea imágenes ni mide
enfoque: usa zonas estáticas registradas en la misma posición y revisa recortes.
Dependencias opcionales en `scripts/requirements-photo.txt`.

```powershell
python scripts/analyze_mgc_photos.py --baseline control1.jpg control2.jpg --candidate candidate1.jpg candidate2.jpg --roi tiles:200,970,950,1040 --output .local-private/comparison.json
```

Fotografías, preferencias completas, seriales, APK, lecturas de memoria y logs
permanecen en `.local-private/`. Los perfiles mínimos y las herramientas son
los únicos componentes fotográficos añadidos al código público.

## Fuentes del port

El port y su implementación pertenecen a BSG:
[publicación V18](https://www.celsoazevedo.com/files/android/google-camera/dev-bsg/f/dl366/),
[catálogo](https://www.celsoazevedo.com/files/android/google-camera/dev-bsg/),
[grupo BSG](https://t.me/publicgroup_mgc_bsg).
V18 describe Google AWB y la corrección de AWB del sistema. Los changelogs de
[V25](https://www.celsoazevedo.com/files/android/google-camera/dev-bsg/f/dl383/6/)
y [V29](https://www.celsoazevedo.com/files/android/google-camera/dev-bsg/f/dl391/2/)
describen ampliaciones del modelo de ruido. Los controles hallados por ingeniería
inversa en V18 no implican que admita todas las funciones documentadas en esas
revisiones posteriores. No se actualizó GCam durante estos ensayos.
