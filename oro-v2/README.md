# Trading Plan v2 — Oro MGC 5m (pullback a la EMA 20 con sesgo)

Backtest del plan publicado en Claude Docs ("Trading Plan v2 — Oro MGC 5m").

## Cómo correrlo

```bash
# 1) poner los exports de NinjaTrader (1 minuto, Last, UTC) en raw/  ->  MGC_MM-AA.Last.txt
python backtest/gold_build.py raw/ data/      # serie continua (front por volumen diario)
python backtest/gold_bt.py data/ resultados/  # versiones de sesgo A/B/C x salidas 2R/1.5R/BE
```

- Señales en velas de 5 m; entradas, stops y objetivos simulados minuto a minuto.
- Costos: $1,84 por contrato ida y vuelta + 1 tick de deslizamiento en entrada, stop y salida por tiempo.
- Se saltan los días de roll / con ventana incompleta y los 2 primeros días tras un hueco de datos.
- Sin filtro de noticias (la ventana arranca 08:45 NY, después de los datos de las 08:30).

## Resultado v0 (ene–jul y oct–nov 2026, 167 días)

| Sesgo | Salida | Trades | % acierto | PF | Esperanza | Neto | DD máx |
|---|---|---|---|---|---|---|---|
| A sin sesgo | 2R | 140 | 33,6% | 0,93 | −0,07R | −$771 | −24,9R |
| B 1h vs EMA50 | 2R | 85 | 41,2% | 1,21 | +0,16R | +$1.321 | −9,9R |
| C oráculo | 2R | 88 | 46,6% | 1,52 | +0,32R | +$3.069 | −6,9R |

Detalle completo en `resultados/resumen.csv` y una planilla de trades por variante.
