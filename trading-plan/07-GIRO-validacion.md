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

## El giro funciona sobre cualquier nivel de sesión (paso 1 de mecanización)

Al mecanizar los pivotes, primero se testeó el giro sobre los **niveles de cada sesión**
(máx/mín), no solo Europa. Sesiones (hora BA → UTC): Asia 15:30–04:00, Europa 04:00–10:00,
NY 10:00–15:30; rango de apertura = 1ª hora de NY (13:00–14:00 UTC). A 2R, sin lookahead:

| Nivel del giro | n | R/trade | PF | Por año |
|---|---|---|---|---|
| **Asia** | 529 | **+0,687** | **2,57** | +0,91 / +0,82 / +0,54 / +0,68 |
| Europa | 392 | +0,393 | 1,74 | +0,20 / +0,49 / +0,24 / +0,54 |
| Apertura NY (post 14:00 UTC) | 342 | +0,312 | 1,56 | +1,40 / +0,34 / +0,22 / +0,38 |

**El giro tiene edge sobre los tres niveles de sesión, positivo todos los años — Asia es el más
fuerte.** Implementado en `backtest.py` (`session_levels` + `backtest_giro(levels=...)`).

> **Nota de método (lookahead cazado).** La 1ª medición del rango de apertura de NY dio +1,40
> R/trade y PF 8 — irreal. La causa: el rango cierra a las 14:00 UTC pero el giro podía dispararse
> *durante* esa hora, usando datos del futuro. Con el guard `min_utc_hour=14` cayó a +0,31,
> consistente con los demás. Es el tipo de error que solo se ve midiendo con rigor.

### Pivotes dinámicos (días anteriores): sin edge mecánico

Se probó el giro sobre **pivotes dinámicos** = máx/mín de sesiones (Asia/EU/NY) de **días
anteriores** que aún no fueron rotos, tomando el giro en el primer cruce de un pivote vivo
(sin lookahead, búsqueda del cruce acotada a 6 días).

| Nivel del giro | n | R/trade | PF | Por año |
|---|---|---|---|---|
| Pivotes dinámicos (días previos) | 63 | **−0,286** | 0,62 | − − ~0 − |

**Negativo.** El edge del giro parece ser el **barrido intradía de la sesión** (el rango de
Asia/Europa se barre en falso en la apertura de NY y revierte). Un nivel viejo no tiene esa
dinámica: al tocarlo, muchas veces el precio lo **rompe de verdad** y sigue, así que fadearlo
pierde. *Salvedad:* es una primera mecanización del pivote; podría refinarse. Pero el contraste
con los niveles de sesión (todos positivos) es fuerte.

**Conclusión (spec del giro para el bot):** el giro automático se dispara sobre **niveles de
sesión del mismo día — Asia, Europa y apertura de NY**. Los pivotes de días anteriores quedan
afuera. Además simplifica el bot.

## Nota de método

También se vio que el sub-requisito de "reingreso al rango" y el de "rechazo por mecha/volumen"
no matchean de forma estricta las entradas reales: varias entradas ocurren **todavía sobre/junto
al nivel**, en la vela de confirmación, sin esperar un cierre limpio de reingreso (p. ej. 10-nov,
entrada larga aún por debajo del EuLow, que además perdió −20). El giro, como se opera, es más
laxo que como se escribió. Esto se calibra cuando se decida el punto anterior.
