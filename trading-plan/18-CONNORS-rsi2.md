# Connors RSI(2) — segundo bot para Sim (edge chico pero validado out-of-sample)

## La estrategia
Reversión a la media de Larry Connors adaptada a futuros, sobre **MES gráfico de 15 minutos**:
- **SMA 200** = filtro de tendencia (largos solo sobre la media, cortos solo debajo).
- **SMA 10** = retroceso de entrada y salida.
- **RSI(2)** = gatillo de timing (cruce extremo del 10 hacia arriba = largo; del 90 hacia abajo = corto).

**Entrada larga:** Close > SMA200 y Close < SMA10 y RSI cruza hacia arriba el 10.
**Entrada corta:** Close < SMA200 y Close > SMA10 y RSI cruza hacia abajo el 90.
**Salida:** el precio vuelve a cruzar la SMA10 (salida Connors). **Stop y target = 30 ticks cada uno (1:1)**
como red de seguridad — Connors no usaba stop, nosotros sí. La salida por SMA10 suele activarse primero.
**Ventana:** 09:00-13:00 hora Argentina, aplanado a las 13:00 (sin overnight). **Miércoles excluido.**

## Por qué este bot y no el ORB de apertura
Probamos en paralelo un ORB de la vela de apertura de EE.UU. Se veía **mejor in-sample**
(+$2.709-$3.076, más frecuencia, positivo los 4 años 2023-2026). Pero al correrlo en el
**out-of-sample 2022-2023 se dio vuelta a −$2.000 / −$2.656**: era un edge **dependiente del régimen**,
no persistente. Lo descartamos antes de arriesgar un peso.

El Connors, en cambio, **pasó el out-of-sample**:

| Período | Datos | Neto (1 MES) | PF | Aciertos |
|---|---|---|---|---|
| In-sample 2023-2026 | continuo | +$474 (30t 1:1) | 2.66 | 74% |
| **Out-of-sample 2022-2023** | contratos sueltos | **+$474** (2022:+$330, 2023:+$144) | **2.66** | 74% |

Positivo en 2022 (bear market) y 2023 — años que ninguna grilla de optimización vio nunca.

## Lo que descartamos por el camino (para no repetirlo)
- **Timeframe:** en 1 min es puro ruido (el costo se come todo). El edge vive en **15-30 min**.
- **Stop/target fijo apretado o ratio negativo:** empeoran. El 1:1 de 30 ticks es lo más robusto.
- **Filtro ADX:** parecía sumar +$110 in-sample pero **restó out-of-sample** — era sobreajuste. Va **sin ADX**.
- **Aflojar RSI, ampliar ventana, incluir miércoles:** todas suben la frecuencia pero **matan el edge**.
- **Otros instrumentos:** MNQ y CL **no funcionan** con este setup (pierden con cualquier stop). Es **solo-MES**.

## Los peros honestos
- Es **chico**: ~$400-600/año en 1 contrato, ~30 operaciones/año (baja frecuencia).
- 2025-2026 fueron ~planos in-sample; la plata OOS salió de 2022-2023.
- Falta confirmarlo **en papel** antes de real.

## Cómo correrlo en Sim101
1. **NinjaTrader en US Eastern** (Tools → Options → General → Time zone). El bot convierte a hora
   Argentina para la ventana (Argentina es UTC-3 fija, sin horario de verano, así que la conversión
   es estable — a diferencia del adaptativo).
2. Compilá `ConnorsRsi2` (F5).
3. New → **Chart**. Instrumento **MES 09-26**. Tipo de barra = **Minute**, valor **15**.
4. *Days to load* = **90** (para que la SMA 200 arranque caliente; overnight/Globex, no solo RTH).
5. Click derecho → **Strategies…** → agregá **ConnorsRsi2**. Propiedades:
   - **Contratos** = 1
   - **Stop / Target (ticks)** = 30 / 30
   - **Inicio / Fin ventana (HHMM ART)** = 900 / 1300
   - **Excluir miércoles** = True
   - **Zona del gráfico** = **Eastern Standard Time** (con NinjaTrader en US Eastern)
   - **Account** = **Sim101**, **Enabled** = True
6. OK. Queda corriendo junto al adaptativo (son estrategias distintas, no se pisan).

## Seguimiento
Es de baja frecuencia: puede pasar días sin operar. Se juzga por **varias semanas / decenas de
operaciones**, no por un día. Respetar siempre $2.500 de tope de drawdown y $900 de pérdida diaria.
Verificá en las primeras operaciones que los horarios de entrada caen dentro de 09:00-13:00 ART
(mirando la hora del gráfico en Este + la conversión).
