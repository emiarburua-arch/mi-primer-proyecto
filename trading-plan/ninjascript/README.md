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

## La entrada es LO que define el edge (hallazgo de la validación)

Comparando la 1ª corrida en NinjaTrader (v1, entrada a mercado) contra Python se descubrió que
**cómo entra el bot cambia todo**:

| Modo de entrada | Winrate | R/trade | PF |
|---|---|---|---|
| Orden STOP en el nivel de ruptura (v2, correcto) | 54 % | **+0,63** | 2,38 |
| Mercado al cierre de la vela (v1, incorrecto) | 35 % | +0,04 | 1,06 |

El v1 entraba tarde (a mercado, después de que la vela ya rompió) y **eso se comía todo el edge**.
La v2 pone una **orden stop que descansa en el nivel** y se llena cuando el precio lo rompe —
que es lo que el plan siempre dijo ("orden limitada al romper"). Si volvés a correr el Strategy
Analyzer con la v2, el winrate debería subir de ~35 % a ~50 % y el PF acercarse a ~2.

## Otras diferencias con el backtest de Python (a reconciliar en Sim)

- **Sizing a $50:** con contratos enteros de MCL el riesgo no queda perfectamente constante
  (A≈$45, B≈$60, C=$50, D=$75). Aceptable para probar.
- **Contrato único en NinjaTrader:** el Strategy Analyzer corre UN contrato; Python usa el
  continuo (front de cada día). Para comparar, correr NT en un rango donde el contrato elegido
  ERA el front (p.ej. MCL Aug26 en jun–jul 2026), no meses donde estaba ilíquido.
- **R para los topes:** se calcula de `ProfitCurrency / riesgo$` de cada trade cerrado.
