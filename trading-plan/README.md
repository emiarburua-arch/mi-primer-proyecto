# TPP EA n01 — revisión del trading plan

Análisis de las planillas B20x50 (backtest y operativa real) y correcciones propuestas
al Trading Plan Personal.

## Resultado en una línea

El sistema pierde porque su winrate real (**22,2 %** sobre 27 operaciones) quedó muy
por debajo del umbral de equilibrio (**35,1 %**), no por gestión ni por disciplina —
26 de las 27 operaciones se ejecutaron según plan.

## Documentos

| Archivo | Contenido |
|---|---|
| [`01-DIAGNOSTICO.md`](01-DIAGNOSTICO.md) | Por qué pierde: los números, el test de significancia, la causa mecánica |
| [`02-PLAN-CORREGIDO.md`](02-PLAN-CORREGIDO.md) | Las siete correcciones (C1–C7), sin tocar la lógica de entrada |
| [`03-CHECKLIST-FASE-1.md`](03-CHECKLIST-FASE-1.md) | Checklist diario y criterios de revisión a las 30 y 60 operaciones |
| `informe.html` | Resumen visual del diagnóstico |

## Datos analizados

129 operaciones en total, desde las planillas en Drive:

- `B20x50 - CL Backtest desde 01-02-2024.xlsx` — 78 ops, +$5.213, WR 57,7 %
- `B20x50 - MES backtest desde 1-02-2024.xlsx` — 24 ops, −$212, WR 29,2 %
- `B20x50 - TPP EA n01.xlsx` — 19 ops reales, −$501, WR 26,3 %
- `B20x50 - Earn2 trade 22-04 EA01 A.xlsx` — 8 ops reales, −$443, WR 12,5 %

## Reproducir el análisis

Los scripts de `analisis/` leen el volcado de texto de cada planilla y recalculan todo:

| Script | Qué hace |
|---|---|
| `parse.py` | Extrae las operaciones de la pestaña «Entrada de Datos» |
| `analyze.py` | Winrate, profit factor, cortes por patrón / hora / día / mes, rachas, drawdown |
| `deep.py` | Test binomial, intervalos de Wilson, ventana horaria ajustada por horario de EE.UU. |
| `sim.py` | Monte Carlo de la prueba de fondeo y cálculo de tamaño de muestra |
| `mes.py` | Backtest de MES por separado |
| `curve.py` | Curvas de resultado acumulado para el informe |

Las rutas a los volcados están al principio de cada script y hay que apuntarlas a los
archivos exportados desde Drive.
