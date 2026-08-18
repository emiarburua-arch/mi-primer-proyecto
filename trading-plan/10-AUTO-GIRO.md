# Auto-GIRO — spec del bot (corazón del sistema)

Definición mecánica y cerrada del giro que va a operar el bot. Es el resultado de mecanizar
la parte discrecional (paso 1): probamos cada tipo de nivel, dejamos los que tienen edge y
descartamos los que no. Implementado en `backtest/backtest.py` (`backtest_giro_multi`).

## Qué dispara el giro

En cada barra M5 de la **ventana del giro** (08:00–11:30 ET), y con tope de **2 operaciones/día**,
el bot busca un giro sobre **los tres niveles de sesión del mismo día**, en este orden:

| Fuente | Nivel | Horas (BA → UTC) | Guarda |
|---|---|---|---|
| **Asia** | máx/mín sesión Asia | 15:30–04:00 → 18:30–07:00 | — |
| **Europa** | máx/mín sesión Europa | 04:00–10:00 → 07:00–13:00 | — |
| **Apertura NY** | máx/mín 1ª hora de NY | 10:00–11:00 → 13:00–14:00 | no antes de 14:00 UTC (evita lookahead) |

**Pivotes dinámicos de días anteriores: NO** (sin edge mecánico; ver `07-GIRO-validacion.md`).

## Mecánica del giro (idéntica en las tres fuentes)

Alcista sobre el **mínimo** del nivel (corto = espejo sobre el máximo):

1. **Manipulación:** una vela perfora el nivel (low < nivel − 1 tick) en las últimas ~12 velas.
2. **Confirmación:** la 1ª vela a favor (verde) después de la manipulación.
3. **Entrada:** orden límite al romper el máximo de la vela de confirmación.
4. **Stop:** distancia fija del escenario (tabla ATR), debajo del pivote (mín. de la
   manipulación). Si el pivote queda más lejos que el stop, **no se opera** (§1.3).
5. **Objetivo:** 2R. **Aplanado** no-overnight a las 21:00 UTC (18:00 BA).

## Evidencia (2,5 años, dic-2023 → jul-2026)

| Auto-giro combinado | Valor |
|---|---|
| n | 651 (~260/año) |
| Winrate | 56 % |
| R/trade | **+0,678** |
| Profit factor | **2,54** |
| R total | **+441 R** |
| Por año | 2023 +1,00 · 2024 +0,84 · 2025 +0,49 · 2026 +0,71 |

Por fuente: Asia +0,71 (n=512) · Europa +0,61 (n=96) · NY +0,47 (n=43). **Positivo todos los
años, sobre las tres fuentes.**

## Advertencias (para no sobrevender)

- El detector **sobre-dispara** respecto de la selección discrecional real (651 vs ~30 giros
  manuales). Mide el edge mecánico, que es justamente lo que el bot ejecuta.
- Modelo v0: stop **pesimista** intrabar (subestima), **sin parciales** (salida única 2R/−1R),
  fills sobre barras M5. Comisión no descontada (chica frente al total, pero existe).
- Un instrumento (CL/MCL), un período macro. Falta validar en NinjaScript (fidelidad Python↔NT)
  y en Sim101 antes de plata real.
- Datos con huecos de segunda quincena; no rompen el resultado pero reducen cobertura.

## Lo que falta para el bot

1. Combinar con la **gestión** (sizing por ATR, bracket OCO, topes −2R día/−3R semana, aplanado).
2. Portar a **NinjaScript** y validar que reproduce este backtest.
3. Correr en **Sim101** antes de cuenta real.
