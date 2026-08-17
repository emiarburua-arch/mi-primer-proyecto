# Backtest v0 — primeros resultados

Primera corrida del motor (`backtest/backtest.py`) sobre la serie continua de CL
**oct-2025 → jul-2026** (~9 meses, 47.368 barras M5). Traduce el gatillo mecánico de
ESTRUC+VC a código y mide el resultado en R.

> **Cómo leer esto.** Son **hipótesis que generó el backtest, no conclusiones para operar.**
> La muestra es corta (~300 trades), el modelo es crudo (v0) y los cortes por dirección/
> escenario reducen el número por celda. Nada de acá cambia el plan todavía. Sirve para saber
> **qué mirar** y para probar con más datos.

---

## 1 · Qué se validó primero

Antes de simular, se comprobó que las reglas **describen** la operativa real:

| Condición de ESTRUC+VC | Presente en las entradas reales (34 con datos) |
|---|---|
| Núcleo: retroceso → vela verde → ruptura de su máximo | **88 %** |
| Estructura HH+HL medida por swings en M5 | ~50–60 % (tope, insensible a parámetros) |

**Lectura:** el gatillo mecánico es fiel (88 %). La **estructura** que el operador lee
visualmente **no se reduce limpio a una regla de M5** — es en parte discrecional / de
temporalidad mayor. Por eso se trata como **filtro a medir**, no como condición a clonar
(igual que la hipótesis A/B, 04-SPEC.md §8).

---

## 2 · Fidelidad: el detector reproduce el winrate real

Corriendo solo el gatillo mecánico en la ventana operativa, con stop del escenario y objetivo 2R:

- **Winrate del detector: 35 %** — prácticamente idéntico al **35,4 % real** del registro B20x50.

Que un detector ciego (sin discrecionalidad) dé el mismo winrate que la operativa real es una
señal fuerte de que **el motor está bien calibrado** y de que el winrate del sistema lo fija
el gatillo, no la selección fina.

---

## 3 · Resultados del gatillo mecánico (sin filtro discrecional)

### 3.1 · El objetivo 2:1 es el mejor de los probados

| Objetivo | Trades | Winrate | R/trade | Profit factor |
|---|---|---|---|---|
| 1,0 R | 324 | 50 % | +0,006 | 1,01 |
| 1,5 R | 317 | 39 % | −0,025 | 0,96 |
| **2,0 R** | **311** | **35 %** | **+0,051** | **1,08** |
| 2,5 R | 303 | 27 % | −0,082 | 0,89 |
| 3,0 R | 296 | 23 % | −0,091 | 0,88 |

**Confirma quedarnos en 2:1.** Estirar a 2,5R empeora claramente (el precio no llega tan lejos
tantas veces). Cierra definitivamente la vieja duda 2:1 vs 2,5:1 — con datos, no con opinión.

### 3.2 · El gatillo crudo es apenas breakeven

A 2R: **R/trade +0,051, PF 1,08**. Es decir: **el gatillo mecánico solo, sin discrecionalidad,
es apenas rentable / breakeven.** Esto es coherente con el diagnóstico original: las pérdidas
reales no venían de un setup negativo, sino de la **inconsistencia del riesgo en dólares**. Con
riesgo fijo $150 (la corrección del plan), el mismo setup queda en breakeven+, y el edge tiene
que venir de la **selección** (estructura + hipótesis) que agrega el humano.

### 3.3 · Cortes que aparecen (a confirmar, NO a operar aún)

| Corte | Trades | Winrate | R/trade |
|---|---|---|---|
| **Largos** | 164 | 38 % | **+0,123** |
| Cortos | 147 | 33 % | −0,030 |
| **Escenario A** (ATR bajo, CL) | 163 | 39 % | **+0,148** |
| Escenario B | 98 | 33 % | −0,020 |
| Escenario C | 28 | 29 % | −0,193 |
| Escenario D | 22 | 32 % | −0,045 |

Dos pistas: los **largos** funcionan mejor que los cortos, y el edge se concentra en el
**escenario A** (baja volatilidad). Encaja con que el registro real ya está sesgado a largos
(65 L / 32 C). **Pero:** son cortes en la misma muestra (in-sample) con celdas chicas
(escenario C = 28 trades). Buscar dónde "brilla" dentro de 300 trades es la receta clásica del
overfitting. Se confirman con **más datos y out-of-sample**, no se adoptan ahora.

---

## 4 · Advertencias del modelo v0 (importantes)

- **Stop pesimista:** si una barra M5 toca stop y objetivo, se cuenta stop. Subestima resultados.
- **Sin parciales:** el registro real usa salidas parciales (l1/l2/l3); acá es salida única a 2R
  o −1R. No modela la gestión real.
- **Sin filtro discrecional:** no incluye estructura fiable ni hipótesis A/B. Mide el piso crudo.
- **Muestra corta:** ~9 meses / ~300 trades. Sin potencia estadística para afirmar edges chicos.
- **Barras M5:** la ejecución intrabar real puede diferir del fill simulado.

---

## 5 · Próximos pasos

1. **Más datos.** Exportar más años de CL (mismo método) para darle potencia real a los cortes.
2. **Parciales.** Modelar la gestión real (l1/l2/l3) y comparar contra salida única a 2R.
3. **GIRO+VC.** Sumar el detector del giro sobre el nivel de Europa (07:00–13:00 UTC), ya
   codificable con los horarios congelados.
4. **Filtro de estructura/hipótesis.** Probar proxies y medir su aporte por separado (§8 del spec).
5. **Out-of-sample / walk-forward.** Confirmar (o descartar) los cortes de §3.3 fuera de muestra.

---

*Reproducir:* `CL_DATA_DIR=<dir con los CSV> python backtest/backtest.py`
(los CSV se generan con `backtest/build_data.py` a partir de los exports de NT).
