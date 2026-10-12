# GCam system installer 0.7.0 — verificación del 12 de octubre de 2026

Se revisó, construyó e instaló el módulo mediante ADB y APatch en el Infinix
Zero X Neo X6810-GL conectado, con Android 16 / API 36. No se utilizó ARTEMIS.

## Cambio

El módulo incluye el APK BSG 9.7 V32 original de Downloads, conservando su firma
y SHA-256 `132e18273b3aafdb93e851f5db88156bd4f82c5032ad8de6594fa5a49ea6fe89`.
Instala el APK y sus 21 bibliotecas ARM64 en `system/priv-app/X6810GCam`.
Únicamente la biblioteca `libgcastartup.so` lleva el arreglo de caché previamente
verificado, con SHA-256
`64cfcb3f598cdf3e75875bdd4cb8e8775a6763be15c3d2240d1d7ee0656f053a`.

Se corrigió la inconsistencia entre el hash del APK original empaquetado y el
hash del APK optimizado exigido por el script anterior. Ya no se monta un APK
modificado sobre el original. No incluye las optimizaciones DEX de 0.5.0.

La lista privilegiada concede exclusivamente `INSTALL_PACKAGE_UPDATES`, que
este APK declara y que el framework del teléfono clasifica como
`signature|privileged`. Los permisos normales los concede Android; el servicio
otorga los runtime y habilita almacenamiento completo, modificación de ajustes
y política No molestar. Los permisos no dependen de la compilación ART.

## Resultado observado

| Comprobación | Resultado |
|---|---|
| Instalación APatch y reinicio real | Módulo 0.7.0 promovido a `/data/adb/modules/x6810_gcam_startup` |
| Overlay | APK original visible en `/system/priv-app/X6810GCam` |
| Paquete activo existente | `SYSTEM`, `UPDATED_SYSTEM_APP` y `PRIVILEGED` |
| Permisos del paquete activo | 32 solicitados, 32 concedidos, ninguno pendiente |
| Runtime | Los 11 declarados concedidos |
| Permiso privilegiado | `INSTALL_PACKAGE_UPDATES: granted=true` |
| App-ops especiales | `MANAGE_EXTERNAL_STORAGE` y `WRITE_SETTINGS`: `allow` por UID y paquete |
| Política No molestar | `cmd notification allow_dnd` completado correctamente |
| APK y biblioteca activos | Hashes coincidentes con el original y el arreglo nativo |
| Compilación ART | `Success`; servicio: permisos 0, optimización 0 |
| Segunda ejecución de concesiones | Omite repetirlas al detectar el marcador de éxito |
| Apertura | Activity iniciada, vista previa visible, sin diálogo de permisos |
| Captura principal | JPEG nuevo guardado y decodificado: 4000×3000 |

La ruta activa sigue en `/data/app` porque GCam ya existía como instalación de
usuario. Android la conserva como actualización de la app privilegiada de
sistema, con los datos anteriores; el script aplica solamente el arreglo nativo
a su biblioteca. No se ejecutó `uninstall-system-updates`, ni se borraron datos.

La instalación desde cero queda implementada mediante el APK incluido y el
escaneo de `priv-app` al reiniciar, pero no se ensayó borrando la instalación
existente. Tampoco se revalidaron otros sensores, vídeo, todos los modos ni
Android 11–15. Esta prueba no demuestra una mejora de velocidad o calidad.

## Artefactos locales

- ZIP final: `dist/x6810-gcam-system-0.7.0.zip` y su archivo `.sha256`.
- Copia del ZIP final en Downloads del teléfono.
- Copia canónica del módulo: `gcam/apatch-startup/gcam.zip`.
- Diagnóstico, auditoría de permisos, captura y respaldos privados:
  `dist/analysis/gcam-system-0.7.0/`.
- Respaldos anteriores a la actualización: `gcam-before-070-data.tar.gz` y
  `gcam-before-070-module.tar.gz`, extraídos al host.

Consulta [las instrucciones del módulo](../gcam/apatch-startup/README.md) para
construcción, instalación y retirada. Los accesos especiales no se revocan
automáticamente al retirar el módulo; pueden retirarse desde Ajustes.
