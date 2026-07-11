# Guía de backtest — EmaCrossoverMES en NinjaTrader 8

Cómo probar la estrategia con datos históricos **antes** de arriesgar un dólar real.
Esta guía asume que ya instalaste y compilaste la estrategia (ver `SETUP.md`).

---

## 1. Requisitos previos

1. **NinjaTrader 8 instalado** (la licencia gratuita alcanza para backtest y simulación).
2. **Una conexión de datos** con histórico de futuros CME:
   - Si ya tenés cuenta con NinjaTrader Brokerage, tu conexión de datos en vivo también
     descarga histórico.
   - Si no, creá una cuenta gratuita en ninjatrader.com: incluye acceso a datos de futuros
     para simulación/backtest.
   - Conectate: **Control Center → Connections → tu conexión**. Sin conexión no se descarga
     histórico.
3. **La estrategia compilada sin errores** (F5 en el NinjaScript Editor).

## 2. Preparar comisiones y datos

### Comisiones (una sola vez)

1. **Control Center → Tools → Commissions**.
2. Creá una plantilla (ej. "MES real") con tu costo real por contrato de MES.
   Referencia típica con exchange fees: **~$0.65–0.80 por lado** (~$1.30–1.60 round-trip).
3. Asignála a tu conexión/instrumento.

### Datos históricos

- El histórico se descarga solo al correr el backtest, pero verificá que tenés datos de
  **1 minuto** y de **tick** para el rango que quieras probar: abrí un chart de MES en 1 min
  y mirá cuánto histórico carga.
- **Importante**: la resolución de fills "High" necesita **datos de 1 tick**. Los proveedores
  suelen ofrecer menos histórico de tick que de minuto (semanas/meses, no años). Estrategia
  práctica: backtest largo (1–2 años) en resolución estándar para una primera criba de
  parámetros, y validación final (últimos 3–6 meses) con resolución High.

## 3. Configurar el Strategy Analyzer

1. **Control Center → New → Strategy Analyzer**.
2. En el panel izquierdo, click derecho → **Backtest**.
3. Configurá:

| Campo | Valor recomendado |
|---|---|
| Strategy | `EmaCrossoverMES` |
| Instrument | El contrato MES vigente (ej. `MES 09-26`) o `MES ##-##` (contrato continuo) |
| Data series | **1 minute** (y repetí con 3 y 5 min para comparar) |
| Time frame | Al menos 6 meses; ideal 12+ |
| Trading Hours | `CME US Index Futures ETH` (la estrategia ya limita su horario internamente) |
| **Order fill resolution** | **High** + serie secundaria de **1 tick** (ver nota arriba) |
| Slippage | **1 tick** |
| Commission | Tu plantilla de comisiones |
| Include commission | ✔ activado |

4. Los parámetros de la estrategia aparecen abajo — dejá los defaults para la primera corrida.
5. Click **Run** (o OK). Los resultados aparecen en las pestañas Summary / Analysis / Trades /
   Chart.

## 4. Cómo leer los resultados

Mirá estas métricas, en este orden:

1. **Total # of trades**: si hay menos de ~100 trades, el resultado no es estadísticamente
   confiable — ampliá el rango de fechas.
2. **Profit factor** (ganancia bruta / pérdida bruta): > 1.25 después de costos empieza a ser
   interesante. Entre 1.0 y 1.15, la estrategia probablemente no sobreviva al slippage real.
3. **Avg. trade** (ganancia media por trade): tiene que superar cómodamente los ~$4 de costos.
   Un avg. trade de $2 con profit factor 1.3 es una estrategia que muere en vivo.
4. **Max. drawdown**: ¿aguantarías esa racha con dinero real? Multiplicalo ×1.5–2 para lo que
   verás en vivo.
5. **Pestaña Trades**: revisá 10–20 operaciones una por una en el chart. ¿Las entradas tienen
   sentido? ¿Los stops son razonables? Esto detecta bugs que las métricas esconden.

## 5. Comparar timeframes (1m vs 3m vs 5m)

Repetí el mismo backtest cambiando solo **Data series**. Para 5 minutos ajustá antes:

- `Max Bars In Trade`: 15 → **6–8**
- `Min ATR (ticks)`: 8 → **16**
- `Session End (HHMM)`: opcionalmente 1130 → **1200–1230** (compensa la menor frecuencia)

Compará profit factor, avg. trade y drawdown entre los tres. El costo relativo por trade
favorece a los timeframes mayores; la frecuencia favorece a los menores.

## 6. Optimización — con mucho cuidado

El Strategy Analyzer también permite **Optimize** (click derecho → Optimize) para barrer
rangos de parámetros. Reglas para no autoengañarte:

1. **Optimizá pocos parámetros a la vez** (2–3 máximo, ej. períodos de EMA y umbral de ADX).
2. **Out-of-sample obligatorio**: optimizá con una parte de los datos (ej. 2024–2025) y validá
   con datos que la optimización nunca vio (ej. 2026). Si el resultado se derrumba
   out-of-sample, estaba sobreajustado.
3. Desconfiá del parámetro "mágico": si EMA 8/21 da profit factor 1.4 pero 9/21 y 8/22 dan
   0.9, ese 1.4 es ruido, no ventaja. Buscá **mesetas** de parámetros buenos, no picos.
4. Usá **Walk-Forward** (pestaña del Analyzer) como prueba final: optimiza y valida en
   ventanas móviles automáticamente, simulando cómo lo operarías de verdad.

## 7. Después del backtest: el circuito completo

```
Backtest (histórico) → Market Replay (opcional) → Sim101 en vivo (2–4 semanas) → Real (1 contrato)
```

1. **Market Replay** (Control Center → Tools → Historical Data → descarga Market Replay):
   reproduce días completos tick a tick y la estrategia opera "en vivo" sobre ellos. Es el
   punto intermedio perfecto entre backtest y simulación.
2. **Sim101 en tiempo real**: activá la estrategia en un chart con la cuenta Sim101 durante
   2–4 semanas. Compará sus resultados con lo que el backtest predijo para ese período — si
   divergen mucho, algo está mal (datos, fills, horario).
3. **Real con 1 contrato** solo si el Sim confirma el backtest. Los límites diarios
   (`MaxDailyLossDollars`, etc.) son tu red de seguridad — no los agrandes al empezar.

## Errores comunes

- ❌ Backtest sin comisiones ni slippage → resultados de fantasía.
- ❌ Resolución estándar con stops/targets que caben en una vela → NinjaTrader adivina cuál se
  tocó primero (suele adivinar a tu favor).
- ❌ Optimizar 6 parámetros sobre 3 meses de datos → curva perfecta que muere en vivo.
- ❌ Probar 50 combinaciones y elegir la mejor sin validación out-of-sample → lo mismo.
- ❌ Saltarse el Sim101 porque "el backtest dio bien" → el mercado cobra la lección.
