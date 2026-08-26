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
