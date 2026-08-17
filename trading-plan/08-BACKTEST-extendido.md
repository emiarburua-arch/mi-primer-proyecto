# Backtest extendido — 13,5 meses (jun-2025 → jul-2026)

Actualización de `06-BACKTEST-v0.md` con más datos: se sumaron 5 contratos hacia atrás
(CL 07-25 … 11-25), llevando la serie continua a **jun-2025 → jul-2026**. La novedad
importante: **con más datos el giro no se rompe, se estabiliza** — la firma de un edge real,
no de un artefacto.

## Cambio clave: el GIRO se estabiliza

| GIRO+VC Europa-only (2R) | 9 meses | **13,5 meses** |
|---|---|---|
| R/trade | +0,380 | **+0,425** |
| Profit factor | 1,71 | **1,81** |
| 1ª / 2ª mitad | +0,08 / +0,67 ⚠️ | **+0,40 / +0,45** ✅ |
| n | 177 | 243 |

Las dos mitades ahora son positivas y parecidas. Además la 1ª mitad es en buena parte
**jun–oct 2025, período NO operado en vivo** → es out-of-sample genuino. Que el edge aparezca
ahí es la mejor señal que tuvimos.

## Resto de resultados (2R, 13,5 meses)

- **ESTRUC+VC** (gatillo mecánico): n=411, WR 37 %, **R/trade +0,094**, PF 1,15. Mitades
  +0,131 / +0,058 → **ambas positivas** (antes la 2ª daba negativa). Modesto pero más consistente.
- **Filtro M60**: sigue **sin ayudar** — ema50 +0,017 < baseline +0,094; slope6/combo con 2ª
  mitad negativa. Confirmado con más datos: no es un filtro válido.
- **Escenario A** (ATR bajo, CL): +0,182 sobre **260 trades** — la pista más robusta.
- **Objetivo 2R** sigue siendo el mejor múltiplo.
- **Filtro de rechazo del giro** (mecha/vol 3×): baja n (243→95) y R/trade (+0,425→+0,277),
  aunque ahora ambas mitades quedan positivas. No es necesario como regla dura.

## Advertencias que siguen vigentes

- 243 giros / 411 estruc en 13,5 meses: mejor, pero no es una muestra enorme; es petróleo 2025-26.
- Los detectores **sobre-disparan** respecto de la selección discrecional real (el giro real
  fueron ~30 operaciones; el detector dispara 243). Se mide el **edge mecánico**, no la selección.
- Modelo v0: stop pesimista intrabar, **sin parciales**, giro **solo sobre Europa** (falta el ⅓
  sobre pivotes).
- El split en mitades es tiempo adyacente, no walk-forward estricto.

## Estado de los datos

Serie continua jun-2025 → jul-2026 con **huecos de segunda quincena** en jun/jul/ago/sep 2025
(los contratos 07-25…11-25 se exportaron a ~15 días cada uno, solo la primera mitad del mes) y
los huecos festivos ya conocidos (dic-2025/ene-2026). No rompen el backtest (se saltan los días
sin datos) pero conviene, al seguir hacia atrás (meta: ene-2024), **exportar cada contrato por
su vida completa (~30 días)** para no dejar quincenas afuera.

## Conclusión operativa (provisional)

El **giro es el candidato fuerte** y es el primero que mejora al agregar datos. La prioridad
sigue siendo **más histórico** (hacia ene-2024) para: (1) confirmar el giro con walk-forward
real, (2) testear la hipótesis de regímenes ESTRUC↔GIRO, (3) darle potencia al escenario A.
