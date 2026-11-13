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

## Resultado v1 (ene–nov 2026, 212 días) — NO aprobado

| Sesgo | Salida | Trades | % acierto | PF | Esperanza | Neto | DD máx |
|---|---|---|---|---|---|---|---|
| A sin sesgo | 2R | 172 | 29,7% | 0,78 | −0,18R | −$3.233 | −46,8R |
| B 1h vs EMA50 | 2R | 109 | 35,8% | 0,98 | +0,00R | −$139 | −23,1R |
| C oráculo | 2R | 104 | 43,3% | 1,34 | +0,22R | +$2.553 | −11,3R |

v0 (sin agosto–septiembre) daba B = +0,16R / PF 1,21: era efecto de la muestra.
Agosto–octubre 2026 costó −21R a la versión B. Incluso con el sesgo perfecto (C),
el motor de pullback a la EMA 20 convierte la dirección en poca ventaja (PF 1,34).

Detalle completo en `resultados/resumen.csv` y una planilla de trades por variante.
