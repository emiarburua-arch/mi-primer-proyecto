# Bot de trading — Micro E-mini S&P 500 (MES) en NinjaTrader 8

Estrategia de cruce de medias móviles exponenciales (EMA) para futuros **MES**, implementada
como un **NinjaScript Strategy** en C# que corre dentro de NinjaTrader 8.

## ⚠️ Advertencia de riesgo

Este bot opera **contratos de futuros con apalancamiento** y, tal como está configurado,
puede conectarse a una **cuenta real** y ejecutar órdenes con dinero real. Una estrategia
de cruce de EMA es intencionalmente simple: **no hay garantía de que sea rentable**. Antes
de arriesgar capital real:

1. Corré el **Strategy Analyzer** de NinjaTrader con datos históricos de MES para ver cómo se
   hubiera comportado la estrategia.
2. Conectá la estrategia a la cuenta simulada **Sim101** (viene por defecto en NinjaTrader) y
   dejala correr en tiempo real con datos de mercado reales durante varios días/semanas.
3. Solo después de eso, seleccioná tu cuenta real en la ventana de control de la estrategia.
4. Empezá con el tamaño mínimo (1 contrato) y con los límites de riesgo activados.

Nadie puede garantizar resultados en mercados de futuros. Operá solo capital que puedas
permitirte perder.

## Qué hace la estrategia (`NinjaTrader/Strategies/EmaCrossoverMES.cs`)

- **Señal de entrada**: EMA rápida (por defecto 9 períodos) cruza por encima de la EMA lenta
  (por defecto 21 períodos) → entra **largo**. Cruce a la inversa → entra **corto**. Solo una
  posición a la vez; si hay una posición contraria abierta, se cierra antes de abrir la nueva.
- **Stop-loss / take-profit por operación**: se fijan automáticamente en ticks al entrar
  (por defecto 40 ticks / 10 puntos de stop, 80 ticks / 20 puntos de objetivo — 1 tick de MES
  = 0.25 puntos = $1.25).
- **Límite de pérdida diaria** (`MaxDailyLossDollars`, por defecto $500): si la pérdida
  realizada + no realizada del día alcanza ese monto, la estrategia **cierra todo y deja de
  operar por el resto de la sesión**.
- **Límite de operaciones por día** (`MaxDailyTrades`, por defecto 10): evita sobre-operar.
- **Ventana de sesión** (`SessionStartHHMM` / `SessionEndHHMM`, por defecto 09:30–15:55 hora
  de mercado): solo opera en el horario regular de mayor liquidez y se aplana antes del
  cierre.

Todos estos valores son parámetros configurables desde la UI de NinjaTrader, no hace falta
tocar el código para ajustarlos.

## Instalación en NinjaTrader 8

1. Abrí NinjaTrader 8.
2. Menú **Tools → Edit NinjaScript → Strategy...** o directamente **New → NinjaScript Editor**.
3. En el editor, **File → Import…** y seleccioná
   `NinjaTrader/Strategies/EmaCrossoverMES.cs` de este repositorio 
   (o copiá el archivo manualmente a `Documentos\NinjaTrader 8\bin\Custom\Strategies\`).
4. Compilá con **F5** (o el botón *Compile*). No debería haber errores.
5. Abrí un chart de **MES** (el contrato vigente, ej. `MES 09-26`) con el timeframe que quieras
   operar (ej. velas de 5 minutos).
6. Click derecho en el chart → **Strategies…** → seleccioná `EmaCrossoverMES` → **Add**.
7. Configurá los parámetros (períodos de EMA, contratos, stops, límites de riesgo, horario).
8. En la pestaña **Account**, elegí primero **Sim101** para probar. Cuando estés listo para
   operar en real, cambiá a tu cuenta de bróker conectada a NinjaTrader.
9. Marcá **Enabled** para activar la estrategia.

## Backtesting

Usá **Strategy Analyzer** (menú Control Center → New → Strategy Analyzer) para correr
`EmaCrossoverMES` sobre datos históricos de MES antes de operarla en vivo. Ajustá los
parámetros ahí y revisá métricas como drawdown máximo, win rate y profit factor antes de
tocar una cuenta real.

## Conexión al bróker

NinjaTrader 8 se conecta a tu cuenta de futuros a través de una **conexión de datos/brokerage**
configurada en **Connections → Connection Guide** (por ejemplo NinjaTrader Brokerage, Rithmic,
CQG, etc., según con quién tengas la cuenta). Esta estrategia no gestiona la conexión al
bróker: opera sobre la cuenta que hayas seleccionado en el paso 8. La configuración de esa
conexión (credenciales, API keys) se hace directamente en NinjaTrader y **nunca debe subirse a
este repositorio**.
