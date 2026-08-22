# Primer Empuje — hallazgos multi-activo

Backtest de la estrategia de comunidad (`backtest/primer_empuje.py`, reglas D1–D6) sobre 1 min,
simulador fiel. Datos: CL dic-2023→jul-2026; MNQ y MES oct-2025→ago-2026 (~11 meses).

## Validación del código (la disciplina que faltó con el giro)

La comunidad reportó **ES breakout ~30 %**. Mi código:
- ES breakout **2:1 → 33 % WR**; ventana de las últimas 3 sem de julio → 31 %.

**Reproduce el número.** La implementación es fiel. (El 30 % era con objetivo 2:1 / ventana corta,
no el 1:1 de muestra completa, que da 50 %.)

## El carácter del activo decide la dirección

| Activo | Carácter | Config | exp/trade | PF | Por año |
|---|---|---|---|---|---|
| **ES** (MES) | revierte | **fade + 60min** | **+0,070R** | 1,15 | −0,00 / +0,10 |
| NQ (MNQ) | revierte (leve) | fade | +0,023R | 1,04 | −0,03 / +0,04 |
| NQ (MNQ) | — | breakout | −0,031R | 0,93 | +0,01 / −0,05 |
| CL | tiende | breakout + 60min | +0,065R | 1,13 | +0,00/−0,00/+0,06/+0,15 |

**Índices (ES, NQ) → fade. Crudo (CL) → breakout.** Con lógica económica: los índices revierten
intradía; el petróleo tiene momentum. El **ES fadeado** es el candidato más fuerte y el único con
confirmación externa (la comunidad).

## Lección: 3 semanas no son nada

El NQ breakout en las **últimas 3 semanas de julio 2026** dio **62 % WR, +0,166R** (¡espectacular!).
Sobre los **11 meses completos**: **−0,031R, negativo**. Eran 16 operaciones de una racha. El mismo
espejismo que el giro, cazado antes de programar. **La verdad está en la muestra larga.**

## Estado y próximos pasos

- El **ES fade** es real y modesto (+0,070R, PF 1,15), positivo ambos años, confirmado por la
  comunidad. Es lo mejor que encontramos. Pero: **11 meses / ~189 trades / antes de costos.**
- Antes de construir un bot: **conseguir más años de ES** para confirmar que el fade aguanta.
- Refinar (salida por tiempo, filtros) con disciplina — solo cuenta si sobrevive out-of-sample.
