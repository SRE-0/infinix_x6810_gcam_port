# Controles manuales y preview de BSG GCam V18

## Resultado de la investigación

Revisión del 10 de octubre de 2026 en X6810-GL, Android 16 GSI, con ADB y
root APatch. No se utilizó ARTEMIS. El usuario precisó que el enfoque sí
cambia la preview, mientras los demás ajustes se reflejan al fotografiar.

La evidencia examinada apunta a la **ruta de peticiones de GCam**, no a una
incapacidad general del HAL para aplicar controles manuales en tiempo real.
No se demostró una solución mediante preferencias o parches vendor. La vía
experimental requería modificar código interno de GCam; se abandonó y se
revirtió en el dispositivo por instrucción del usuario.

No se obtuvo una mejora fotográfica verificable ni se publicó un módulo nuevo.

## APK y entorno comprobados

- Paquete: `com.android.MGC_9_7_047`.
- Versión instalada: `9.7.047.702121536.18`.
- SHA-256 del APK:
  `132e18273b3aafdb93e851f5db88156bd4f82c5032ad8de6594fa5a49ea6fe89`.
- Módulo RAW/HD48/flash activo: `x6810_raw12mp`, v001.
- Módulo adicional encontrado: `x6810_camera_ros`, 0.3.0 experimental.

Se utilizó el APK extraído de esta instalación para el análisis DEX; no se
asumió que las clases de otros APK históricos fueran equivalentes. Los
módulos APatch y los binarios vendor no se escribieron durante esta sesión.

## Evidencia de preview y captura

En el ensayo actual, la interfaz mostró **ISO 1000** seleccionado, pero el
resultado de preview registrado por `dumpsys media.camera` conservó:

```text
android.control.aeMode       ON
android.control.awbMode      AUTO
android.sensor.sensitivity   1138
android.sensor.exposureTime  30001000 ns
```

La selección manual de la interfaz no basta, por tanto, para concluir que la
preview está recibiendo una petición Camera2 manual. El volcado también
contiene plantillas y metadatos estáticos; no deben confundirse sus valores
con los resultados del flujo activo.

Una captura de diagnóstico durante la selección manual produjo un JPEG con
EXIF ISO 300 y exposición 71,879 ms. Es una observación de captura, no una
validación de igualdad entre los controles, la preview y todos los fotogramas
del HDR+. La fotografía se retiró del teléfono al deshacer la sesión.

## Trabajo previo recuperado

El ensayo privado del 2 de octubre ya incluía una aplicación Camera2 con
YUV y RAW simultáneos. En la principal y el telefoto se observaron 30/30
resultados estabilizados dentro de la tolerancia del ensayo para ISO y
exposición manuales. En la principal, con 5 ms, pasar de ISO 100 a ISO 800
cambió la media YUV de luminancia aproximadamente de 8,3 a 51,5. Con ISO 100,
pasar de 5 a 20 ms también cambió la luminancia. Los presets AWB modificaron
las ganancias y las componentes cromáticas YUV en ambos sensores.

Es evidencia de comportamiento físico en esos ensayos, más fuerte que el
simple eco de metadatos. **No es una prueba nueva de esta sesión**, ni valida
la frontal, todos los modos de GCam o todas las combinaciones de streams.

Los ensayos históricos de HDR+ desactivado y HDRNet no dejaron una corrección
demostrada de este problema. Tampoco debe confundirse con el cuello de cola
RAW corregido en v0.11 al aumentar el mínimo de buffers: fluidez y transmisión
de controles manuales son problemas distintos.

## Ruta encontrada en el código instalado

Los nombres siguientes son los del DEX analizado, no una API estable:

| Punto | Papel observado |
|---|---|
| `jxu.d` / `jxu.e` | Estado de selección de ISO / exposición; la exposición se almacena en ns. |
| `iqi` → `ArkInfo` | Pasa la selección manual al cálculo de captura HDR+. |
| `ljr` | Construye peticiones de captura con AE OFF, ISO y exposición estándar desde `FrameRequest`. |
| `jsf.z` | Actualiza parámetros del servidor de frames; contiene tratamiento explícito del enfoque manual. |
| `RamPatcher.set_pthcr` | Aplica el mapa de parches de procesamiento documentado en los perfiles V18. |

La decompilación de `jsf.z` presenta una condición aparentemente contradictoria
para activar AE manual. Debido a la ofuscación, no se considera por sí sola
una prueba definitiva de un defecto: el dato operativo confirmado es que la
preview observada siguió en AE automático. Además, un puente añadido solamente
a esa actualización no consiguió que el cambio de ISO se reflejara en ella;
la propagación del estado manual también requiere investigación interna.

Google AWB, correcciones de color y factores del lib patcher pertenecen al
procesamiento de GCam. No son equivalentes a cambiar directamente el AWB,
denoise o matrices del ISP MediaTek. El trabajo previo verificó que algunos
factores del patcher se escriben en memoria después del primer disparo.
Forzar valores vendor no reproduce automáticamente la preview del HDR+
multiframe ni su JPEG final.

Esto es compatible con una limitación de la implementación de preview de
este APK. No demuestra que todos los ports BSG tengan el mismo comportamiento.
La [publicación de BSG V18](https://www.celsoazevedo.com/files/android/google-camera/dev-bsg/f/dl366/)
identifica la revisión; no aporta por sí sola una garantía de preview manual.

## Ensayos de esta sesión y retirada

1. Se observó el estado manual con Frida 17.18.0 y un puente Java. Varias
   sesiones terminaron en SIGSEGV; una prueba con desoptimización global de
   ART permitió observar actualizaciones, pero no estableció una solución
   estable. No se dejó instrumentación persistente.
2. Se construyó un APK experimental local, conservando las entradas originales
   salvo `classes.dex` y `classes2.dex`. Se montó temporalmente sobre el APK
   instalado con APatch, sin sobrescribirlo ni reinstalar el paquete.
3. La primera variante no corrigió la preview de ISO. Se preparó otra variante
   para propagar el estado manual; su transferencia falló por permisos y no
   llegó a montarse. El usuario indicó abandonar modificaciones internas.
4. Se retiró el montaje temporal. El desmontaje ordinario informó recurso
   ocupado; se detuvo GCam y se retiró mediante desmontaje diferido. La
   comprobación posterior del namespace de zygote no encontró el montaje.

La reconstrucción local no constituye un APK firmado válido para instalar
como actualización oficial. No se distribuye ni se propone como solución.

## Estado final comprobado

- El APK vuelve a tener exactamente el SHA-256 original indicado arriba.
- No queda el montaje de prueba en el namespace de zygote.
- Frida está detenido y se retiró el forwarding ADB creado para la sesión.
- Se eliminaron del teléfono el APK temporal, el script de montaje y los
  archivos auxiliares creados por esta investigación.
- Se eliminó la fotografía de prueba a través de MediaStore y se restauró
  únicamente el indicador de galería desplazado por esa captura.
- GCam quedó detenido, descartando los controles manuales transitorios.
- No se instalaron módulos, no se alteraron calibraciones y no se modificaron
  preferencias fotográficas de ruido/color de los perfiles del proyecto.

Logs, XML, captura de diagnóstico, DEX, prototipos descartados y comprobaciones
de retirada permanecen en `.local-private/manual-preview-20261010/`. Los
binarios y datos privados no forman parte de una entrega pública.

La investigación se cierra sin parche activo: continuar esta vía exigiría
trabajo interno en GCam, expresamente excluido por el usuario.
