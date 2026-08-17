# Validación del GIRO+VC contra las operaciones reales

Se cruzaron los **24 giros reales con datos** contra el nivel de Europa (máx/mín de la
ventana 07:00–13:00 UTC = 04:00–10:00 BA) para ver si el setup, tal como está escrito en
§6.2.1 del plan, describe lo que se opera.

## Resultado

| Condición | Presente |
|---|---|
| Perforan el nivel de Europa dentro de ~10 velas **y** entran cerca del nivel | **62 %** (15/24) |
| **NO tocan Europa** — el giro es sobre otro nivel (pivote dinámico) | **33 %** (8/24) |

Ejemplos que confirman el mecanismo de Europa (perforación → confirmación → ruptura):
04-nov, 17-nov, 21-nov, 25-nov, 02-dic. Ejemplos que **no** tocan Europa: 05-nov (entrada en
61.0 con EuLow en 60.21, a ~80 ticks) y 14-nov.

## El hallazgo (y la decisión pendiente)

El plan (§6.2.1) define el giro como un setup **exclusivo del nivel de Europa**. Pero **1 de
cada 3 giros reales no está sobre Europa** — están sobre otros niveles (probablemente pivotes
dinámicos). Es una **discrepancia entre la regla escrita y la operativa real**, justo el tipo
de ambigüedad que el plan buscaba eliminar.

**Decisión requerida antes de codificar el detector del giro:**

- Si los giros fuera de Europa son **intencionales** → el detector necesita también los
  **pivotes dinámicos** (definirlos y calcularlos; más trabajo).
- Si son **desvíos** → el giro queda Europa-only, y queda registrado un dato duro: **~⅓ de los
  giros se salen del plan**, lo que por sí solo es material para la revisión.

## Backtest del giro Europa-only (9 meses)

Detector del giro sobre el nivel de Europa integrado en `backtest/backtest.py`
(`backtest_giro`): manipulación (perfora el nivel) → confirmación (1ª vela a favor) → entrada
al romper su extremo, stop del escenario debajo del pivote. Ventana 08:00–11:30 ET (más
temprana que ESTRUC, porque el barrido ocurre en la apertura de NY). **No** incluye los giros
sobre pivotes (≈⅓). A objetivo 2R:

| Variante | Total | 1ª mitad | 2ª mitad |
|---|---|---|---|
| sin filtro de rechazo | +0,380 R/trade (n=177, WR 46 %, PF 1,71) | **+0,08** | **+0,67** |
| con filtro de rechazo (mecha ≥60 % o vol ≥3×) | +0,184 (n=72, WR 40 %) | +0,10 | +0,30 |

**Lectura honesta:**

1. El número total se ve muy bien (+0,38 R/trade), **pero el edge está casi todo en la 2ª
   mitad** (+0,67 vs +0,08). Misma firma de inestabilidad que invalidó el filtro M60: no se
   puede concluir con 9 meses.
2. **Contraste con ESTRUC:** la 2ª mitad fue negativa para ESTRUC (continuación) y muy positiva
   para el giro (reversión). Sugiere un **cambio de régimen** en la 2ª mitad (más choppy /
   reversión). Real o ruido: hay que confirmarlo con más datos.
3. **El filtro de rechazo (mecha/volumen 3×) no se justifica en esta muestra:** corta la mitad
   de los trades y baja el R/trade. Queda como opción medible, no como regla dura.

## Nota de método

También se vio que el sub-requisito de "reingreso al rango" y el de "rechazo por mecha/volumen"
no matchean de forma estricta las entradas reales: varias entradas ocurren **todavía sobre/junto
al nivel**, en la vela de confirmación, sin esperar un cierre limpio de reingreso (p. ej. 10-nov,
entrada larga aún por debajo del EuLow, que además perdió −20). El giro, como se opera, es más
laxo que como se escribió. Esto se calibra cuando se decida el punto anterior.
