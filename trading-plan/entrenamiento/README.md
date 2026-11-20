# Entrenamiento – calibración de reglas con ejemplos

Objetivo: comprobar que las reglas de la sección 8 del plan leen el gráfico igual que el trader.

## Capturas

Guardar en `capturas/` con el nombre: `AAAA-MM-DD_HHMM_concepto_valida|invalida.png`

Ejemplo: `2026-10-14_1005_manipulacion_valida.png`

### Qué debe verse en la captura (NinjaTrader)

- Eje de precios y eje de tiempo visibles.
- Temporalidad del gráfico (5m o 60m) visible.
- El nivel dibujado (ej. mínimo de Europa) y el máximo y mínimo de la sesión de referencia.
- Marcas: perforación 1, perforación 2, reingreso.

### Ficha de cada captura (copiar en `ejemplos.md`)

```
## 2026-10-14 10:05 – manipulación – VÁLIDA / INVÁLIDA
- Nivel: mínimo de Europa
- Sesión de referencia: Europa  | máximo: 21100,00 | mínimo: 21000,00
- Extremo de la perforación: 20988,50
- Perforaciones: 2
- ¿La tomaría? sí / no
- Por qué:
```

Incluir también **contraejemplos**: casos que parecían manipulación pero se descartaron.
