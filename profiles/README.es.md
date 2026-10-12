[English](README.md) | **Español**

# Perfil recomendado: X6810-GL / BSG 9.7 V32

**[x6810-gcam-bsg-9.7-v32-recommended.xml](x6810-gcam-bsg-9.7-v32-recommended.xml)**
es el archivo aportado por el propietario como `recomend_settings.xml`, renombrado
para indicar dispositivo, port, versión y propósito. Su contenido se conserva
byte a byte; no se retocaron los ajustes durante esta documentación.

| Dato | Valor |
|---|---|
| Port probado | [MGC_9.7.047_V32_MGC.apk](https://1-dontsharethislink.celsoazevedo.com/file/filesc/MGC_9.7.047_V32_MGC.apk) |
| Paquete | `com.android.MGC_9_7_047` |
| Dispositivo/sistema probado | Infinix X6810-GL, Android 16 GSI |
| Resultado | Funciona perfectamente, Probado en Android 16 GSI |
| Formato | XML SharedPreferences, raíz `map` |
| Preferencias | 755: 727 string, 11 boolean, 10 int y 7 long; sin nombres duplicados |
| Tamaño | 47 229 bytes |
| SHA-256 XML | `1b4014581d5bc07b0b3678ba4cea6be7e3bef7cd7f532e51d02e8907aa0ee9f9` |
| SHA-256 APK del builder de sistema | `132e18273b3aafdb93e851f5db88156bd4f82c5032ad8de6594fa5a49ea6fe89` |

## Cargar el perfil en la GCam externa

1. Instala la APK V32 enlazada como app normal y concede los permisos solicitados.
   El módulo GCam de sistema es opcional; el módulo RAW/OIS/HD48 pertenece al
   [otro repositorio](https://github.com/SRE-0/infinix_x6810_raw).
2. Descarga el XML conservando la extensión `.xml`. Puedes guardarlo en una
   carpeta accesible, por ejemplo Downloads.
3. En los ajustes de BSG, guarda/exporta primero tu configuración actual mediante
   `Save config`. Abre la sección de configuraciones y usa `Load config` para
   seleccionar el XML recomendado. Los nombres del menú pueden estar traducidos.
   BSG documenta carga desde cualquier carpeta en su
   [guía de ajustes](https://www.celsoazevedo.com/files/android/google-camera/dev-bsg/help/0/).
4. Vuelve a abrir la app si la carga lo requiere y selecciona los sensores
   disponibles. El perfil conserva `lens_wl_key=0,1,2` del equipo probado.
5. Para volver a tus preferencias carga el XML que exportaste antes.

No copies el archivo directamente a `/data/data` ni uses el aplicador antiguo
de V18: este es un snapshot amplio para importar desde BSG, no el overlay parcial
de 16 strings que manejaba aquella herramienta. El release entrega el XML
separado; instalar el módulo GCam no aplica las preferencias automáticamente.

## Ajustes relevantes y alcance

| Preferencia | Valor guardado | Interpretación |
|---|---|---|
| `camera.ois_forced_photo_mode` | boolean `true` | Solicita OIS en fotografía; OIS del teleobjetivo probado y funcionando |
| `pref_video_stabilization_ois_key` | string `1` | Preferencia OIS de vídeo, distinta de la de fotografía |
| `camera.lenstoggles_enable` | boolean `true` | Controles de selección de lentes |
| `lens_wl_key` | `0,1,2` | IDs de cámara del equipo probado |
| `pref_camera_raw_output_option_available_key` | `1` | Disponibilidad de la opción RAW |
| `pref_camera_raw_output_key` | `0` | Guardado RAW/DNG desactivado en este snapshot; actívalo en la app si lo necesitas |
| `pref_video_resolution` | `RES_1080P` | Preferencia de resolución de vídeo |

También conserva ajustes de AWB, exposición, reducción de ruido, nitidez y
parámetros del lib patcher. Los sufijos `_0`, `_1` y `_2` son las preferencias
por cámara de esa configuración; no se trasplantan automáticamente a otros
dispositivos o ports. El XML incluye estado interno (contadores, flags de inicio,
versión y una URI de miniatura local). No es un respaldo de APK, fotos o datos
completos; esa URI no apunta a una imagen incluida en el repositorio.

Las pruebas corresponden a V32 y Android 16 GSI. No se ejecutaron nuevas pruebas móviles al renombrarlo. Puedes
instalar otras GCam externas compatibles, pero este perfil no certifica todas
sus versiones ni Android 11. JPEG HD48 debe solicitarse como stream JPEG por la
app; el perfil no convierte RAW en 48 MP ni fuerza a todas las GCam a usar HD48.

## Referencias históricas V18

`x6810-gcam-bsg-v18-recommended.xml` y `gcam-bsg-v18.json` quedan como experimentos
anteriores. No son el perfil recomendado V32 ni se incluyen como XML principal
del release actual. `tools/configure_mgc_photo.py` aplica sus overlays V18 y
no debe usarse para importar este snapshot V32.
