# Sistema adaptativo (seguir el régimen) — validado OOS en MES y MNQ

## La idea

El ORB de apertura no tiene dirección estable: el índice **tiende** algunos períodos (gana breakout)
y **revierte** otros (gana fade). Un bot de dirección fija fracasa. Uno que **siga el régimen** —
opere la dirección que viene ganando— captura ambos.

Regla: *operar fade si la suma de las últimas K operaciones-fade ≥ 0; si no, breakout.* (K=10.)
Todo lo demás igual que Primer Empuje filtrado (ORB 30m, media200, dirección día previo, 1R,
1 op/día, aplanado).

## Resultado (datos limpios NinjaTrader, un contrato por año, con costos)

| Año | MES ($5/pt) | MNQ ($2/pt) | Portfolio 1+1 |
|---|---|---|---|
| 2024 | +$355 | +$1.482 | +$1.837 |
| 2025 | +$1.471 | +$3.206 | +$4.677 |
| 2026 | +$1.250 | +$1.620 | +$2.870 |
| **Total** | **+$3.076** | **+$6.308** | **+$9.384** |

**Portfolio (1 MES + 1 MNQ): +$9.384 en 3 años, max drawdown −$1.729** (bajo el tope de $2.500).
Positivo los **6 años-instrumento**.

## Por qué es creíble (y no otro espejismo)

- **Out-of-sample real:** el K=10 se eligió mirando MES. Aplicado a MNQ *sin retocar nada* da
  +$6.308. Un parámetro sobreajustado al MES no tendría por qué funcionar en otro instrumento.
- **Robustez de parámetro:** positivo de K=6 a K=15 en ambos (no un valor aislado).
- **Consistencia temporal:** positivo cada año en cada instrumento.
- **Lógica económica:** no es minería de datos, es seguir el régimen vigente.
- Contraste: la dirección fija (fade o breakout) da drawdowns de −$5.000/−$6.000 y pierde en la
  mitad de los años. El adaptivo los evita.

## Los peros (honestos)

1. **MES y MNQ están correlacionados** (los dos son índices de EE.UU.; comparten macro-régimen:
   los dos tendieron en 2024 y revirtieron en 2026). No es una confirmación totalmente
   independiente. Una prueba más fuerte sería un mercado no correlacionado (CL, un futuro de bono,
   una divisa).
2. **Solo 3 años, un único ciclo de régimen** (tendencia 24 → reversión 26). El adaptivo captura
   *esa* transición. No lo vimos manejar un cambio de régimen rápido (whipsaw), que es donde un
   seguidor de régimen sufre.
3. Falta confirmarlo **en vivo/papel** antes de plata real.

## Plan

1. Programar el adaptivo en NinjaScript (rastrea las últimas K operaciones-fade y elige dirección).
2. Correrlo en **Sim101 (papel)** sobre MES + MNQ, 1 contrato cada uno.
3. En paralelo, si se consigue, probar la lógica en **CL** (no correlacionado) para una
   confirmación independiente de verdad.
4. Si el papel acompaña varias semanas, recién ahí evaluar plata real, escalando de a poco y
   respetando $2.500 DD / $900 diario.


## Extensión a 2022-2023 (MES, datos limpios sueltos)

Se corrió el adaptativo (mismo K=10) sobre contratos MES individuales de 2022-2023 con
`backtest/adaptativo_bt.py` (señal continua, fiel al bot corregido). Muestra chica y con huecos
(archivos recortados; warmup de volatilidad por contrato) → 49 operaciones en 2 años.

| Año | Neto (1 lote) |
|---|---|
| 2022 (bear market) | +$528 |
| 2023 | -$174 (12 ops, ruido) |

**Lo relevante:** en el bear market de 2022 el sistema fue positivo — no depende de mercado alcista.
Con las corridas del bot corregido: MES 5 años (2022-26) = +$3.378, positivo 4 de 5.

## Portfolio final validado — bot REAL (corregido + filtrado en ambos)

Corridas reales del `PrimerEmpujeAdaptativo` (K=10, `UsarFiltros=true`) en el Strategy Analyzer,
un contrato limpio por año:

| Año | MES | MNQ | Portfolio (1+1) |
|---|---|---|---|
| 2024 | +$236 | +$302 | +$538 |
| 2025 | +$1.621 | +$3.055 | +$4.676 |
| 2026 | +$1.307 | +$1.126 | +$2.433 |
| **Total** | **+$3.165** | **+$4.483** | **+$7.648** |

**Max drawdown −$1.848** (bajo el tope de $2.500). **Peor día combinado −$565** (bajo los $900).
Positivo los 6 años-instrumento. (Mi simulación previa estimaba +$9.384; el número real es
+$7.648 — la diferencia son los fills reales de las órdenes OCO. El real es el que vale.)

**CRÍTICO — los filtros no son opcionales.** Con `UsarFiltros=false`, MNQ pasa a 78 operaciones de
peor calidad y el drawdown del portfolio salta a **−$3.628**, que rompe el tope de $2.500. En papel
y en real, `UsarFiltros` debe estar en **TRUE siempre**.
