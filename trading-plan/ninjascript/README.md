# ninjascript/ — el bot en NinjaTrader 8

`GiroSystem.cs` — estrategia NinjaScript que implementa el sistema auto-giro validado en
`../backtest` (ver `../10-AUTO-GIRO.md` y `../11-SISTEMA-completo.md`).

> **Estado:** v1 para compilar y validar. **No fue compilado todavía** — es esperable iterar
> sobre errores de compilación. No operar con plata real hasta validar en Sim101.

## Instalación

1. NinjaTrader 8 → **New → NinjaScript Editor**.
2. Botón derecho en **Strategies → New Strategy** (o importá el `.cs`): pegá el contenido de
   `GiroSystem.cs` y **compilá** (F5). Iteramos juntos sobre los errores que salgan.

## Requisito CRÍTICo: zona horaria

El código asume que las barras están en **UTC**. Configurá:

> **Tools → Options → General → Time zone = "(UTC) Coordinated Universal Time"**

Si tu NinjaTrader está en otra zona, la lógica de sesiones (Asia/Europa/NY) no coincidirá con
el backtest. Este es el primer punto a verificar.

## Instrumento

Diseñado para **MCL (Micro WTI)** — un solo instrumento, contratos escalados por escenario según
el riesgo. El input `Valor tick MCL ($)` debe ser **1.0** (MCL: $1 por tick de 0,01).

## Parámetros (inputs)

| Input | Default | Qué es |
|---|---|---|
| Riesgo por operación ($) | 50 | riesgo objetivo; los contratos se calculan solos |
| Objetivo (R) | 2.0 | múltiplo del stop |
| Máx operaciones/día | 2 | tope diario |
| Tope semanal (R) | −3.0 | al tocarlo, no abre más esa semana |

## Validar (el paso que importa)

1. **Strategy Analyzer** (backtest) sobre CL/MCL, 5 min, período que tengas. Comparar el trade
   log contra el backtest de Python: ¿mismas entradas (fecha/hora/dirección), mismos resultados?
2. Ajustar diferencias (fills, redondeos, zona horaria) hasta que reproduzca razonablemente.
3. Recién ahí, **Sim101** (paper) en un chart de 5 min.

## Diferencias conocidas con el backtest de Python (a reconciliar)

- **Entrada:** el backtest entra a `ruptura + 1 tick` cuando una vela posterior rompe el extremo;
  esta v1 entra **a mercado al cierre de la barra** que rompe. Diferencia chica, a medir en Sim.
- **Stop pesimista:** el backtest, si una barra toca stop y target, cuenta stop; NT usa la
  ejecución real. El bot debería salir un poco mejor que el backtest, no peor.
- **Sizing a $50:** con contratos enteros de MCL el riesgo no queda perfectamente constante
  (A≈$45, B≈$60, C=$50, D=$75). Es aceptable para probar.
- **R para los topes:** se calcula de `ProfitCurrency / riesgo$` de cada trade cerrado; en Sim
  puede diferir levemente del R teórico por comisión/slippage.
