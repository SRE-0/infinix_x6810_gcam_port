# Investigación de arranque de BSG 9.7

Trabajo aislado del módulo RAW, realizado el 11 de octubre de 2026 mediante
ADB y root APatch, sin ARTEMIS. **No contiene un arreglo de rendimiento
demostrado ni un APK o módulo instalable.** Todos los ensayos de preferencias
se revirtieron; ART quedó en `speed-profile`.

El informe está en [GCAM_STARTUP_20261011.md](../../docs/GCAM_STARTUP_20261011.md).
Los APK, ELF, fotos, XML y trazas privados permanecen en
`dist/analysis/startup-20261011/`, excluido de Git.

## Herramientas de diagnóstico

- `preference_trial.py`: ensayo reversible de dos preferencias booleanas,
  con respaldo por dispositivo/clave, lectura de verificación y recuperación.
  Edita únicamente la entrada seleccionada; deja GCam detenida.
- `summarize.py`: resume los registros de `scripts/collect_mgc_startup.py`.
  No interpreta el aviso de ModeSwitcher como una medición de TTFD.
- `audit_native.py`: desensambla JNI del ELF extraído; requiere pyelftools y
  capstone en el directorio indicado con `--deps`.
- `probe_segmenter.py` y `segmenter_cache_probe.js`: observación temporal con
  Frida 17.18.0, sin escrituras a parámetros, buffers o binarios. El offset
  nativo sólo corresponde al APK SHA-256
  `132e18273b3aafdb93e851f5db88156bd4f82c5032ad8de6594fa5a49ea6fe89`.
  La instrumentación puede alterar tiempos y bloquear una inicialización GPU;
  esos registros no deben mezclarse con benchmarks sin instrumentación.
  El script detiene GCam si la retirada de los hooks no termina en cinco segundos.
  El servidor y su cierre son responsabilidad del operador; no se instala en boot.

Ejemplo de ensayo, **no configuración recomendada**:

```powershell
python gcam/startup/preference_trial.py apply --serial SERIAL --key gate --value false --backup-dir dist/analysis/startup/prefs
python scripts/collect_mgc_startup.py --serial SERIAL --label gate-trial --screenshots= --seconds 8
python gcam/startup/preference_trial.py restore --serial SERIAL --key gate --backup-dir dist/analysis/startup/prefs
python gcam/startup/summarize.py dist/analysis/startup
```

No usar `--screenshots=` para concluir que la preview estaba lista: sólo evita
la carga adicional de `screencap` durante la medición de primera presentación.
