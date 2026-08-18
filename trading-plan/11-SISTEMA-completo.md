# Simulación del sistema completo (auto-giro + gestión)

Foto de cómo habría evolucionado la cuenta operando **el sistema entero**: el auto-giro
(`10-AUTO-GIRO.md`) más la gestión — topes como máquina de estado, riesgo fijo $150, MCL con
comisión. Implementado en `backtest/account_sim.py`.

## Reglas de gestión aplicadas

- Máx **2 operaciones/día** (ya viene del detector) → dos stops = −2R = día cerrado.
- **Tope semanal −3R**: si la semana toca −3R, se cierra (no se abren más).
- Riesgo **$150** por operación; **MCL**, contratos por escenario (A=10, B=5, C=3, D=2).
- Comisión MCL **$1,84** round-turn por contrato (incluida en el P&L).

## Resultados (dic-2023 → jul-2026)

| | Sin tope semanal | **Con tope −3R (sistema completo)** |
|---|---|---|
| Operaciones | 651 | 590 |
| Winrate | 56 % | 56 % |
| Profit factor | 2,18 | **2,19** |
| R total | +441 | **+401** |
| **P&L** | +$55.884 | **+$50.907** |
| **Drawdown máx** | $1.771 (11,8 R) | **$1.721 (11,5 R)** |
| Peor día | −$337 | −$337 |
| Peor semana | −$1.234 | **−$560** |
| Racha perdedora máx | 11 | **9** |

Por año (con tope): 2024 +$21.328 · 2025 +$12.333 · 2026 +$15.649. **Positivo todos los años.**

## Lectura

1. **El tope semanal funciona:** cuesta ~$5k de ganancia pero **corta la peor semana a la mitad**
   (−$560 vs −$1.234) y acorta la racha perdedora. Menos retorno, mucho menos riesgo de cola.
2. **Drawdown máx ~$1.721:** muy manejable para una cuenta de fondeo (suelen permitir $2–3k).
3. **Racha de 9 pérdidas seguidas:** durísima a mano, trivial para un bot. Argumento para automatizar.

## Salvedades (no tapar)

- Backtest **idealizado**: sin slippage de entrada, ejecución perfecta, el bot toma **todas** las
  señales (a mano es imposible; por eso es un bot).
- Stop **pesimista** intrabar (subestima), pero falta validar en **NinjaScript + Sim101**.
- Un instrumento, 2,5 años, un período macro. **El pasado no garantiza el futuro.**
- Drawdown medido sobre equity de operaciones cerradas.

## Lo que sigue

Port a **NinjaScript** (session levels + auto-giro + esta gestión) y validar que reproduce este
resultado; después **Sim101** antes de cuenta real.
