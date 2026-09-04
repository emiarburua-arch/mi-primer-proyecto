# ORB de apertura USA — bot en OBSERVACIÓN (falló out-of-sample, no operar en real)

## La estrategia
Ruptura del rango de apertura de EE.UU. sobre **MES, gráfico de 1 minuto**:
- Vela de referencia = primeros **30 min de la RTH (09:30-10:00 hora del Este)**.
- Al cerrar: **buy stop en el máximo** del rango, **sell stop en el mínimo** (OCO, entra el primero).
- **Stop inicial = extremo contrario** del rango (riesgo = el rango de la vela, ~20pt en promedio).
- **Break-even a +50 ticks (12,5pt)**: el stop pasa a la entrada. Sin target, se deja correr.
- **Salida por tiempo 13:00 ART.** 1 operación por día. Miércoles incluidos. Sin filtros.

## ⚠️ Por qué está en OBSERVACIÓN y no validado
Esta es la lección más importante del proyecto, repetida:

| Período | Datos | Neto (1 MES, BE +50t) | PF |
|---|---|---|---|
| In-sample 2023-2026 | continuo | **+$3.076** (positivo los 4 años) | 1.30 |
| **Out-of-sample 2022-2023** | contratos sueltos | **−$2.000** (2022:−$1.565, 2023:−$435) | 0.83 |

In-sample se veía **mejor que el Connors** (más plata, más frecuencia, todos los años en verde).
Pero fuera de muestra **se dio vuelta a negativo** y rompía el drawdown. Es un edge **dependiente
del régimen** (funcionó 2024-2026, falló en el bear market 2022 y en 2023), no persistente.

**Conclusión:** se lleva a Sim101 **solo para observarlo en papel** en paralelo, para ver cómo se
comporta en vivo y aprender. **No se opera en real.** El bot validado para real es `ConnorsRsi2`.

## Lo que sí aprendimos (y quedó en el bot)
- **Anclar a la apertura real de USA** (9:30 ET) fue mejor que un horario fijo argentino: el WR
  subió de 47% a 54% (la vela de apertura verdadera tiene mejor estructura).
- **El trailing stop lo rompe**: convierte los runners (de donde vive el sistema) en ganancias
  chicas. WR sube pero el neto se da vuelta a negativo. NO usar trailing en momentum.
- **El break-even ancho (+50t) sí ayuda**: mejora todo in-sample y reduce pérdidas también OOS.
  Es gestión de riesgo real; por eso quedó activado. Pero no alcanza para salvar el sistema.

## Cómo correrlo en Sim101 (solo observación)
1. NinjaTrader en **US Eastern** — **OBLIGATORIO y verificalo**. El bot NO convierte zonas: usa la
   hora del gráfico tal cual, así que si NinjaTrader no está en US Eastern los horarios quedan mal
   (fue el bug que dejaba posiciones overnight en el primer backtest).
2. Compilá `OrbApertura` (F5).
3. Chart **MES 09-26**, barras de **1 minuto** (fills precisos de la ruptura y el break-even).
4. *Days to load* = 10-30 (no necesita media larga).
5. Strategies → **OrbApertura**. Propiedades:
   - **Contratos** = 1
   - **Apertura RTH (HHMM ET)** = 930, **Minutos del rango** = 30
   - **Break-even a +N ticks** = 50
   - **Aplanado (HHMM ET)** = 1200 (≈13:00 ART en verano; poné 1100 para 13:00 ART en invierno)
   - **Account** = **Sim101**, **Enabled** = True
6. Corré los tres bots en Sim si querés (adaptativo + Connors + ORB) y compará varias semanas.

## Idea a futuro (si querés seguir con el ORB)
El sistema falla en régimen de reversión/whipsaw (2022). Una versión que **siga el régimen**
—como hicimos con el adaptativo del Primer Empuje— podría fadear la ruptura cuando el fade viene
ganando. Es el camino natural si el ORB te interesa: no dirección fija, sino adaptativa.
