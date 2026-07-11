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

Scalping de tendencia pensado para un **chart de 1 minuto de MES** durante las **primeras 2
horas** después de la apertura del mercado americano (09:30–11:30 hora de mercado).

Una operación solo se abre cuando **coinciden cuatro condiciones**:

1. **Dirección de tendencia**: la EMA rápida cruza a la EMA lenta.
2. **Fuerza de tendencia** (define qué es "una tendencia"): el **ADX** está por encima de
   `TrendAdxThreshold`. Debajo de ese valor el mercado está lateral y no opera.
3. **Tendencia de mayor timeframe**: el precio de **60 minutos** está del lado correcto de su
   EMA (largos solo si está por encima, cortos solo si está por debajo). Evita operar contra la
   tendencia dominante.
4. **Volatilidad**: el **ATR** está dentro del rango `[MinAtrTicks, MaxAtrTicks]`. Filtra
   mercado muerto (sin recorrido) y mercado demasiado errático.

### Parámetros

**1. Trend / Signal**
- `FastEmaPeriod` / `SlowEmaPeriod` (por defecto 8 / 21): las EMAs cuyo cruce da la señal.
- `Contracts` (1): tamaño de la posición.

**2. Trend Strength — define qué es una tendencia**
- `TrendAdxPeriod` (14) / `TrendAdxThreshold` (20): solo opera si ADX ≥ umbral.
- `EmaSlopeLookbackBars` (3) / `MinEmaSlopeTicks` (1): la EMA lenta debe haber avanzado al
  menos esos ticks en la dirección del trade durante las últimas N velas (la "base" ya tiene
  que apuntar hacia donde entramos; evita cruces en mercado plano).

**3. Higher-Timeframe Filter — tendencia de 60 min**
- `UseHigherTimeframeFilter` (true): activa/desactiva el filtro. Con `false` opera solo con las
  condiciones de 1 minuto.
- `HtfMinutes` (60): timeframe de la serie de confirmación.
- `HtfEmaPeriod` (50): EMA sobre la serie de 60 min. Solo permite **largos** si el cierre de 60
  min está por encima de esa EMA, y **cortos** si está por debajo.

**4. Volatility — define la volatilidad del mercado**
- `AtrPeriod` (14): período del ATR.
- `MinAtrTicks` (8 ≈ 2 puntos) / `MaxAtrTicks` (40 ≈ 10 puntos): rango de volatilidad válido
  para operar. 1 tick de MES = 0.25 puntos = $1.25. El mínimo de 8 ticks garantiza que cada
  trade tenga recorrido suficiente para pagar comisiones y slippage (~$4 por round-trip).

**5. Exits — salidas adaptadas a la volatilidad**
- `StopAtrMultiple` (1.0) / `TargetAtrMultiple` (1.5): stop y objetivo en múltiplos de ATR
  (riesgo/beneficio dinámico según la volatilidad, no ticks fijos).
- `BreakevenTriggerAtrMultiple` (0.65; 0 = desactivado): mueve el stop cerca de la entrada
  cuando el precio avanza ese × ATR a favor.
- `BreakevenOffsetTicks` (2): el stop de break-even se coloca esos ticks *más allá* de la
  entrada, para que un trade "scratcheado" cubra las comisiones en vez de cerrar en pérdida
  neta.
- `MaxBarsInTrade` (15; 0 = desactivado): time-stop, cierra la operación tras N velas si no
  tocó stop ni objetivo.

**6. Daily Risk — controles diarios**
- `MaxDailyLossDollars` ($300): kill-switch; al alcanzar esa pérdida (realizada + abierta)
  cierra todo y no opera más ese día.
- `MaxDailyTrades` (15): tope de operaciones por día.
- `MaxConsecutiveLosses` (3): frena el día tras esa racha de pérdidas seguidas.
- `CooldownBars` (1): velas de espera tras cerrar antes de volver a entrar.
- `MaxDailyProfitDollars` (0 = desactivado): al alcanzar esa ganancia diaria (realizada +
  abierta) cierra todo y bloquea el día en verde.

**7. Session — ventana horaria y noticias**
- `SessionStartHHMM` (940) / `SessionEndHHMM` (1130): opera solo en esa franja y se aplana al
  salir de ella. Arranca 09:40 para dejar pasar los primeros minutos caóticos del open (y que
  el ATR deje de arrastrar velas de la sesión anterior). Ajustá estos valores a tu **zona
  horaria de la plataforma** (ver nota abajo).
- `UseNewsBlock` (true) / `NewsBlockStartHHMM` (958) / `NewsBlockEndHHMM` (1005): ventana sin
  entradas nuevas alrededor de los datos económicos de las 10:00 ET (ISM, confianza del
  consumidor, etc.). Las posiciones abiertas siguen gestionadas por sus stops.

Todos estos valores son parámetros configurables desde la UI de NinjaTrader, no hace falta
tocar el código para ajustarlos.

> **Nota sobre el horario**: `SessionStartHHMM`/`SessionEndHHMM` usan la hora del reloj de los
> datos en NinjaTrader (definida por tu Trading Hours template y la zona horaria de la
> plataforma). Si tu NinjaTrader no está en horario del Este de EE. UU. (ET), ajustá estos
> valores para que representen 09:30–11:30 ET. Verificá con un chart de MES que las velas de la
> apertura caen donde esperás.

## Instalación en NinjaTrader 8

1. Abrí NinjaTrader 8.
2. Menú **Tools → Edit NinjaScript → Strategy...** o directamente **New → NinjaScript Editor**.
3. En el editor, **File → Import…** y seleccioná
   `NinjaTrader/Strategies/EmaCrossoverMES.cs` de este repositorio 
   (o copiá el archivo manualmente a `Documentos\NinjaTrader 8\bin\Custom\Strategies\`).
4. Compilá con **F5** (o el botón *Compile*). No debería haber errores.
5. Abrí un chart de **MES** (el contrato vigente, ej. `MES 09-26`) en **velas de 1 minuto**
   (la estrategia está calibrada para ese timeframe).
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

**Configuración obligatoria para que el backtest no mienta** (en velas de 1 min el stop y el
target suelen caber dentro del rango de una misma vela, y en resolución estándar NinjaTrader
*adivina* cuál se tocó primero):

- **Order Fill Resolution = High**, con serie secundaria de **1 tick**.
- **Commission**: cargá tu plan real de comisiones de MES (típicamente ~$1.30–1.60 por
  round-trip con exchange fees).
- **Slippage**: al menos **1 tick** por lado.

Sin estos tres ajustes, cualquier resultado positivo del backtest es ficción. Los costos son
el factor decisivo en trades tan cortos.

## Conexión al bróker

NinjaTrader 8 se conecta a tu cuenta de futuros a través de una **conexión de datos/brokerage**
configurada en **Connections → Connection Guide** (por ejemplo NinjaTrader Brokerage, Rithmic,
CQG, etc., según con quién tengas la cuenta). Esta estrategia no gestiona la conexión al
bróker: opera sobre la cuenta que hayas seleccionado en el paso 8. La configuración de esa
conexión (credenciales, API keys) se hace directamente en NinjaTrader y **nunca debe subirse a
este repositorio**.
