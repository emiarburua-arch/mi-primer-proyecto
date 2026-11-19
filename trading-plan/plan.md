# Trading Plan – Micro E-mini Nasdaq-100 (MNQ)

> Estado: **BORRADOR v0.8** – en definición. No se testea nada hasta cerrar todos los `PENDIENTE`.
> Horarios en hora de Nueva York (ET).

---

## 0. Filosofía

Operar el movimiento del precio leyendo el **rango de las velas**. Se construye una narrativa de arriba hacia abajo
(Semanal → Diario → 4h → 60m) y se ejecuta en 5m. Las temporalidades **no necesitan estar alineadas**: cada una cuenta
una parte de la historia, y la entrada en 5m se toma a favor de esa historia.

---

## 1. Concepto base: modelo de velas A-B-C

Se aplica igual en cualquier temporalidad (D, 4h, 60m).

- **A** = vela de referencia (define el rango: máximo `A.high`, mínimo `A.low`).
- **B** = vela siguiente, cuyo cierre respecto al rango de A define el escenario.
- **C** = vela actual (en formación), sobre la que se proyecta el sesgo.

### 1.1 Escenario CONTINUACIÓN (B cierra *out of balance*)

| Condición de B | Sesgo para C | Objetivo |
|---|---|---|
| `B.close > A.high` | Alcista (continuación) | Proyección del rango de A (ver abajo) |
| `B.close < A.low` | Bajista (continuación) | Proyección del rango de A (ver abajo) |

**Objetivos de continuación (P1) – solo como referencia.** Se proyecta el tamaño del rango de A (`R = A.high − A.low`)
desde el extremo roto:

| Referencia | Alcista | Bajista |
|---|---|---|
| 100% | `A.high + 1·R` | `A.low − 1·R` |
| 200% | `A.high + 2·R` | `A.low − 2·R` |
| 300% | `A.high + 3·R` | `A.low − 3·R` |

Si el precio continúa, se toma la siguiente proyección (200%, 300%, etc.).

### 1.2 Escenario REVERSIÓN (B *activa el rango* de A)

**Definición de rango:** el rango de A es su máximo (`A.high`) y su mínimo (`A.low`).

**Activar un rango:** la vela B **perfora** un extremo de A, **vuelve a ingresar** dentro de A y **cierra dentro** de A.
Al activarse, el **extremo contrario** de A queda marcado como objetivo.

| Condición de B | Extremo activado | Sesgo | Objetivo |
|---|---|---|---|
| `B.low < A.low` y `A.low ≤ B.close ≤ A.high` | Inferior | Alcista (reversión) | `A.high` |
| `B.high > A.high` y `A.low ≤ B.close ≤ A.high` | Superior | Bajista (reversión) | `A.low` |

### 1.3 Rangos activos (memoria de la narrativa)

Un rango activado **no se borra** porque la vela C no llegue al objetivo. La historia se va encadenando:

- Cada activación crea un **rango activo** con: temporalidad, vela A de origen, extremo activado, objetivo y fecha/hora.
- Pueden convivir **varios rangos activos a la vez** (en la misma o distintas temporalidades).
- Si se activa un rango nuevo, el anterior **sigue activo** hasta que se cierre.
- Un rango activo se cierra cuando **el precio alcanza su objetivo**.
- **Invalidación (P5 – discrecional):** un rango activo se invalida cuando el mercado **continúa sin darle importancia**
  al rango (sigue su camino sin reaccionar hacia el objetivo). Lo decide el trader.
  - `PENDIENTE P5-proxy` – Regla objetiva que aproxime esta decisión, para poder testearla (ver propuestas en la conversación:
    distancia recorrida en contra, cierre fuera de A por el lado activado, o N velas sin avanzar hacia el objetivo).
  - Mientras tanto, cada invalidación discrecional se registra en el diario (fecha, temporalidad, rango, motivo) para
    poder comparar después con la regla objetiva.
- **Renovación semanal (P5b):** cada semana se buscan **nuevos rangos y objetivos**. Un rango de semanas anteriores
  que sea importante y **no haya sido desactivado** puede mantenerse en la narrativa (decisión discrecional).
- **Prioridad (P5c):** si hay rangos activos con objetivos opuestos, manda el de **mayor temporalidad** (ver sección 3.1).

### 1.4 Casos especiales

- **Inside bar (P2):** B queda dentro de A sin perforar ningún extremo → **neutral**. Se observa cómo se mueve la
  siguiente vela.
  - **P2b:** la inside bar **no ocupa lugar** en la secuencia A-B-C; la vela siguiente toma su rol:
    - Si la inside bar es la vela **B** (dentro de A) → la siguiente vela pasa a ser la vela **B** (se compara contra A).
    - Si la inside bar es la vela **C** (dentro de B) → la siguiente vela pasa a ser la vela **C**.
- **Outside bar (P3):** B perfora **ambos** extremos de A y cierra dentro → **no activa ningún rango**.

---

## 2. Contexto semanal

### 2.1 Niveles

- **PWH / PWL** – máximo y mínimo de la semana anterior (marcados en 60m).
- **MH / ML** – máximo y mínimo del último lunes.

### 2.2 Posición del precio

| Estado | Definición |
|---|---|
| Por encima de la semana anterior | precio `> PWH` |
| Dentro de la semana anterior | `PWL ≤ precio ≤ PWH` |
| Por debajo de la semana anterior | precio `< PWL` |

`PENDIENTE P6` – ¿Cómo condiciona este estado la operativa? (ej. solo largos por encima, ambos lados dentro, etc., o solo es información para la narrativa).

### 2.3 Manipulación de un extremo

Si el precio **manipula un extremo** (semanal o del lunes), lo probable es que vaya hacia el extremo opuesto.

**Manipular (P7)** es el mismo concepto que **activar un rango**, aplicado a los niveles semanales y del lunes, con dos
diferencias:

- **No hace falta una sola vela:** puede ser un **conjunto de velas** que se mantiene del otro lado del nivel.
- Puede haber **varias perforaciones**: ej. una caída perfora el nivel, una nueva caída lo vuelve a perforar, y luego
  el precio sale al alza de vuelta dentro del rango → manipulación del extremo inferior, objetivo el extremo superior.
- **Cuánto perforó** se define de forma **discrecional**.
- `PENDIENTE P7b` – ¿En qué temporalidad se lee la vuelta dentro del rango (60m, 4h)? ¿Qué confirma que la manipulación
  terminó: un cierre de vela de nuevo dentro del rango?
- `PENDIENTE P8` – ¿Si PWH/PWL y MH/ML dan lecturas opuestas, cuál manda?

---

## 3. Narrativa multi-temporalidad

Orden de lectura: **Semanal → Diario → 4h → 60m → 5m (ejecución)**.

### 3.1 Jerarquía de temporalidades (P5c)

Cuanto **mayor** la temporalidad, más **de fondo** es la dirección que marca su rango activo:

- **Diario** = un trasatlántico: la dirección cambia lento y pesa mucho. Marca la dirección y el objetivo **de la semana**.
- **4h / 60m** = la dirección y los objetivos intermedios dentro de esa semana.
- **5m** = una lancha rápida: el sesgo cambia rápido. Es el gráfico **de operativa** (ejecución).

Si hay rangos activos con objetivos opuestos, **manda el de mayor temporalidad** como dirección de fondo.

- **Operar en contra del fondo (P9):** **permitido**, pero solo hasta un **objetivo de temporalidad menor** (ej. el
  objetivo de 60m).
  - **Riesgo (P9b):** el mismo que cualquier trade, **siempre 150 USD**.
- **Objetivo alcanzado (P10):** cuando una temporalidad alcanza su objetivo, se **pasa al siguiente objetivo**.
  - `PENDIENTE P10b` – ¿Cómo se elige el "siguiente objetivo"? (ej. el objetivo de otro rango activo de la misma
    temporalidad, el siguiente nivel semanal/lunes, o el de la temporalidad inmediatamente inferior).

---

## 4. Niveles de sesión (en 5m)

| Sesión | Horario (ET) |
|---|---|
| Asia | 18:00 – 03:00 |
| Europa | 03:00 – 09:30 |
| América | 09:30 – 16:00 |

Se marcan máximo y mínimo de cada sesión.

---

## 5. Gatillos de entrada (5m)

### 5.1 Entrada tipo 1 – Giro tras barrida de sesión

Con sesgo/narrativa **alcista**:
1. El precio barre el **mínimo de la sesión Asia o Europa**.
2. Se **confirma el giro**: el precio **reingresa por encima del nivel barrido** con una **subida de volumen** (P12c).
   - La subida de volumen se evalúa **a ojo**, comparando con el volumen que se viene teniendo **en el día** (discrecional).
3. Se espera un **retroceso** (alcanza con una vela en contra).
4. Al **cierre de la primera vela verde** del retroceso, se espera la **confirmación** (la vela siguiente rompe su máximo).
5. Entrada (ver 5.4).

**En el giro no hace falta estructura** de máximos y mínimos más altos (P12b). La estructura de 5.3 aplica a la
entrada tipo 2.

Bajista: inverso (barrida del máximo de Asia o Europa, reingreso por debajo del nivel con subida de volumen,
primera vela roja del retroceso, ruptura de su mínimo).

### 5.2 Entrada tipo 2 – Retroceso en continuación

Con la continuación ya iniciada en dirección deseada:
1. Se espera un **retroceso**: alcanza con **una vela** en contra (P13).
2. Se espera una **nueva vela en dirección deseada**.
3. Se espera la **vela de confirmación** (5.3).
4. Entrada → ver 5.4.
- La continuación se lee con la **estructura** (ver 5.3).

### 5.3 Vela de confirmación

**Ventana de oportunidad + confirmación (P15).** Ejemplo para **compra**:

1. **Estructura:** impulso que deja un máximo (H1) → retroceso que deja un mínimo (L1) → nuevo impulso con un máximo
   más alto (H2 > H1) → retroceso con un mínimo más alto (L2 > L1).
2. En ese retroceso (L2), la **primera vela que cierra en verde** (`close > open`) es la **vela de referencia**.
3. La **vela siguiente** que **rompe el máximo** de esa vela verde es la **vela de confirmación** → entrada.

**Venta:** inverso. Máximos y mínimos más bajos (L2 < L1, H2 < H1); en el retroceso, primera vela que cierra en rojo;
la vela siguiente que rompe su mínimo es la confirmación.

- **Sin confirmación (P15c):** si la vela siguiente **no** rompe el máximo de la vela verde, se espera una **nueva vela
  verde** con su confirmación, **siempre que la estructura siga siendo válida**.

### 5.4 Tipo de orden de entrada (P12)

Igual para la entrada tipo 1 (giro) y tipo 2 (continuación):

1. Se espera que la **vela de confirmación rompa** el máximo de la vela verde de referencia (compra) o el mínimo de la
   vela roja de referencia (venta).
2. **Recién después de la rotura**, se coloca una **orden limit**:
   - Compra: **1 tick por debajo del máximo** de la vela verde.
   - Venta: **1 tick por encima del mínimo** de la vela roja.
3. La entrada se ejecuta si el precio **retrocede** hasta ese precio.

Ejemplo compra: máximo de la vela verde = 21000.00 → la vela de confirmación lo rompe → orden limit en **20999.75**.

- **Vigencia (P12d):** la orden limit dura **solo durante la vela de confirmación**. Si no se ejecuta antes del cierre
  de esa vela, se cancela.

### 5.5 Ventana horaria de ejecución

Solo las **dos primeras horas de la sesión americana: 09:30 – 11:30 ET** (P16).

---

## 6. Gestión del trade

- **Stop loss (P17):** el stop es de **distancia fija**. Condición obligatoria: tiene que quedar **más allá del último
  retroceso (último pivote)**: debajo en compras, encima en ventas. Si queda más lejos del pivote, mejor (P17b).
  - `PENDIENTE P17c` – ¿Cuál es la distancia fija del stop (en puntos) y cuántos micros se operan?
  - `PENDIENTE P17d` – Si el pivote queda **más lejos** que el stop fijo (el stop quedaría dentro del retroceso), ¿se
    descarta el trade?
- **Take profit (P18):** fijo a **2:1** (2 veces la distancia entre entrada y stop).
  - Los objetivos de rangos y niveles dan la **dirección/narrativa**, no el take profit.
- **Break-even / parciales (P19):** **nunca**. El stop no se mueve y no se toman parciales.
- **Salida (P20):** una vez colocado, el trade se cierra solo por stop o target. **Única excepción:** si llega el
  **final de la sesión americana (16:00 ET)** con el trade abierto, se cierra manual. No se dejan posiciones para el
  día siguiente.

---

## 7. Gestión de riesgo

- **Cuenta (P21):** cuenta de fondeo, **prueba de 50.000 USD**.
  - `PENDIENTE P21b` – Reglas de la prueba: objetivo de ganancia, drawdown máximo (trailing o estático) y límite de
    pérdida diaria de la firma, para verificar que el plan las respeta.
- **Riesgo por trade (P22):** **150 USD** (1R = 150 USD), en todos los trades, también los que van contra la
  dirección de fondo.
- **Límites diarios (P23):**
  - Máximo **3 trades** por día.
  - Pérdida máxima diaria: **2R (300 USD)**. Al llegar, no se opera más ese día.
- **Días y noticias (P24):**
  - **No se opera en feriados de EE. UU.**
  - Con noticias: **no se opera desde 5 minutos antes** de la noticia, y se vuelve a operar cuando el precio
    **recupera la estabilidad** (evaluado a ojo, discrecional).
  - `PENDIENTE P24b` – ¿Qué noticias cuentan? (ej. solo alto impacto de EE. UU.: CPI, NFP, FOMC, PPI, etc.).

---

## Registro de decisiones

| Fecha | Decisión |
|---|---|
| 2026-11-18 | Sesgo por modelo de velas A-B-C (continuación si B cierra fuera de A; reversión si B activa un extremo de A y cierra dentro, objetivo el extremo opuesto). |
| 2026-11-18 | Las temporalidades no necesitan estar alineadas: se lee una narrativa. |
| 2026-11-18 | Entradas en 5m: barrida de máx/mín de Asia o Europa + vela de confirmación; o retroceso en continuación + vela en dirección + confirmación. |
| 2026-11-18 | Niveles semanales (PWH/PWL) y del lunes (MH/ML) se usan para ubicar el precio y detectar manipulación de un extremo → objetivo el extremo opuesto. |
| 2026-11-19 | P4 cerrado: activar un rango = B perfora un extremo de A, vuelve a ingresar y cierra dentro de A; objetivo = extremo contrario de A. |
| 2026-11-19 | Los rangos activados quedan activos aunque C no llegue al objetivo; pueden convivir varios rangos activos. |
| 2026-11-19 | P5: la invalidación de un rango activo es discrecional (el mercado continuó sin darle importancia). Se registra en el diario; queda pendiente una regla objetiva que la aproxime. |
| 2026-11-19 | P5c: a mayor temporalidad, dirección más de fondo (trasatlántico vs lancha). Se opera en 5m; las temporalidades mayores dan dirección y objetivo de la semana. |
| 2026-11-19 | P9: se permite operar en 5m contra la dirección de fondo, solo hasta un objetivo de temporalidad menor y con menor riesgo. |
| 2026-11-19 | P10: al alcanzar un objetivo se pasa al siguiente objetivo. |
| 2026-11-19 | P2: inside bar = neutral, se observa la siguiente vela. P3: outside bar no activa ningún rango. |
| 2026-11-19 | P5b: cada semana se buscan nuevos rangos y objetivos; rangos importantes no desactivados pueden mantenerse. |
| 2026-11-19 | P7: manipular = activar un rango sobre niveles semanales/lunes; puede darse en varias velas y varias perforaciones; profundidad discrecional. |
| 2026-11-19 | P15: confirmación = estructura de máximos/mínimos más altos, primera vela verde en el retroceso, vela siguiente que rompe su máximo. |
| 2026-11-19 | P1: objetivos de continuación = proyecciones del rango de A (100%, 200%, 300%…), solo como referencia. |
| 2026-11-19 | P15c: sin confirmación se espera nueva vela verde + confirmación mientras la estructura siga válida. |
| 2026-11-19 | P12: entradas siempre con orden stop limit a 1 tick de la rotura de la vela de confirmación. |
| 2026-11-19 | P2b: la inside bar no ocupa lugar en la secuencia; la vela siguiente toma su rol (B o C). |
| 2026-11-19 | P12: orden stop limit 1 tick por debajo del máximo de la vela verde (compra) / 1 tick por encima del mínimo de la vela roja (venta). |
| 2026-11-19 | P12b: en la entrada por giro no hace falta estructura; giro confirmado → retroceso → primera vela verde → confirmación → entrada. |
| 2026-11-19 | P12 corregido: tras la rotura de la vela de confirmación se coloca orden limit 1 tick por debajo del máximo de la vela verde (compra) / por encima del mínimo de la roja (venta). |
| 2026-11-19 | P12c: giro confirmado = reingreso por encima/debajo del nivel barrido con subida de volumen. |
| 2026-11-19 | P13: retroceso = alcanza con una vela en contra. P14: la continuación se lee con la estructura. |
| 2026-11-19 | P11: Asia 18:00–03:00, Europa 03:00–09:30, América 09:30–16:00 (ET). P16: entradas solo 09:30–11:30 ET. |
| 2026-11-19 | P12d: la orden limit dura solo durante la vela de confirmación. P12c: volumen evaluado a ojo contra el volumen del día. |
| 2026-11-19 | P17: stop en el último pivote. P18: take profit fijo 2:1. P19: sin break-even ni parciales. P20: cierre manual al final de la sesión americana si sigue abierto. |
| 2026-11-19 | P17b: stop de distancia fija, siempre más allá del último pivote. |
| 2026-11-19 | P21: cuenta de fondeo, prueba 50k. P22/P9b: 150 USD por trade, siempre. P23: máximo 3 trades y 2R de pérdida diaria. |
| 2026-11-19 | P24: no se opera feriados de EE. UU.; con noticias, pausa desde 5 min antes hasta que el precio se estabilice (a ojo). |
