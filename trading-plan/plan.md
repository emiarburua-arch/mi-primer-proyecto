# Trading Plan – Micro E-mini Nasdaq-100 (MNQ)

> Estado: **v1.2** – reglas definidas, incluida la versión objetiva para validación automática (sección 8).
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
  al rango (sigue su camino sin reaccionar hacia el objetivo). Lo decide el trader. **Queda discrecional, sin regla
  objetiva.**
  - Cada invalidación se registra en el diario (fecha, temporalidad, rango, motivo).
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

**Uso (P6):** este estado **no condiciona** la operativa directamente; es **información para formular la hipótesis**
de la semana.

### 2.3 Manipulación de un extremo

Si el precio **manipula un extremo** (semanal o del lunes), lo probable es que vaya hacia el extremo opuesto.

**Manipular (P7)** es el mismo concepto que **activar un rango**, aplicado a los niveles semanales y del lunes, con dos
diferencias:

- **No hace falta una sola vela:** puede ser un **conjunto de velas** que se mantiene del otro lado del nivel.
- Puede haber **varias perforaciones**: ej. una caída perfora el nivel, una nueva caída lo vuelve a perforar, y luego
  el precio sale al alza de vuelta dentro del rango → manipulación del extremo inferior, objetivo el extremo superior.
- **Cuánto perforó** se define de forma **discrecional**.
- **Temporalidad (P7b):** la manipulación y el reingreso se leen en **60m**. La operativa siempre se ejecuta en **5m**.
- **Conflicto de niveles (P8):** si los niveles de la semana anterior (PWH/PWL) y los del lunes (MH/ML) dan lecturas
  opuestas, **mandan los del lunes**.

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
  - **Siguiente objetivo (P10b):** el que **esté primero** (el más cercano en la dirección del movimiento).

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
  - **Tres tamaños de stop (P17c)**, siempre arriesgando **150 USD** (MNQ: 1 tick = 0,25 pts = 0,50 USD por micro):

    | Stop | Puntos | Riesgo por micro | Micros | Riesgo total | Target 2:1 |
    |---|---|---|---|---|---|
    | 75 ticks | 18,75 | 37,50 USD | **4** | 150 USD | 150 ticks (37,5 pts) = 300 USD |
    | 150 ticks | 37,5 | 75,00 USD | **2** | 150 USD | 300 ticks (75 pts) = 300 USD |
    | 300 ticks | 75 | 150,00 USD | **1** | 150 USD | 600 ticks (150 pts) = 300 USD |

  - El tamaño se elige **según la volatilidad, medida con el ATR(14) de 60m (P17e, P17g)**, en **puntos** (unidad de
    precio que muestra la plataforma):

    | ATR | Stop |
    |---|---|
    | menor a 100 | 75 ticks (4 micros) |
    | de 100 a 200 | 150 ticks (2 micros) |
    | mayor a 200 | 300 ticks (1 micro) |

  - **Si el stop que corresponde por ATR no cubre el pivote, el trade se descarta (P17d, P17f).** No se cambia a un
    stop más grande.
- **Take profit (P18):** fijo a **2:1** (2 veces la distancia entre entrada y stop).
  - Los objetivos de rangos y niveles dan la **dirección/narrativa**, no el take profit.
- **Break-even / parciales (P19):** **nunca**. El stop no se mueve y no se toman parciales.
- **Salida (P20):** una vez colocado, el trade se cierra solo por stop o target. **Única excepción:** si llega el
  **final de la sesión americana (16:00 ET)** con el trade abierto, se cierra manual. No se dejan posiciones para el
  día siguiente.

---

## 7. Gestión de riesgo

- **Cuenta (P21):** cuenta de fondeo, **prueba de 50.000 USD**.
  - **Reglas de la prueba (P21b):**

    | Regla | USD | En R (1R = 150 USD) |
    |---|---|---|
    | Objetivo de beneficio | 3.000 | 20R |
    | Drawdown máximo (trailing) | 2.500 | 16,7R |
    | Pérdida diaria máxima de la firma | 1.000 | 6,7R |

    El límite propio del plan (2R = 300 USD por día) queda muy por debajo del límite diario de la firma.
- **Riesgo por trade (P22):** **150 USD** (1R = 150 USD), en todos los trades, también los que van contra la
  dirección de fondo.
- **Límites diarios (P23):**
  - Máximo **3 trades** por día.
  - Pérdida máxima diaria: **2R (300 USD)**. Al llegar, no se opera más ese día.
- **Días y noticias (P24):**
  - **No se opera en feriados de EE. UU.**
  - Con noticias: **no se opera desde 5 minutos antes** de la noticia, y se vuelve a operar cuando el precio
    **recupera la estabilidad** (evaluado a ojo, discrecional).
  - Solo cuentan las noticias de **alto impacto** (P24b).

---

## 8. Reglas para validación automática

Versión objetiva de las partes discrecionales, para poder validar con datos históricos. En vivo se puede seguir
leyendo a ojo; estas reglas son las que usa el código.

### 8.1 Manipulación de un nivel (barrida válida)

Aplica a:

| Nivel | Temporalidad de lectura | Rango de referencia para el 15% |
|---|---|---|
| Máx/mín de sesión (Asia, Europa) – entrada tipo 1 (5.1) | 5m | Rango de esa sesión |
| Máx/mín de la semana anterior (PWH/PWL) – sección 2.3 | 60m | Rango de la semana anterior |
| Máx/mín del lunes (MH/ML) – sección 2.3 | 60m | Rango del lunes |

Una barrida de un nivel es **manipulación válida** si se cumplen las dos condiciones:

1. **Máximo 2 perforaciones** del nivel. Si lo perfora una tercera vez, ya no es manipulación válida.
   - **Separación entre perforaciones (V1):** entre una perforación y la siguiente, al menos **una vela de la
     temporalidad de lectura** (5m para sesiones, 60m para semana/lunes) cierra de vuelta dentro del nivel. Varias
     velas seguidas del otro lado del nivel cuentan como una sola perforación.
2. **Profundidad máxima: 15% del rango de referencia** (la sesión, semana o lunes a la que pertenece el nivel). Si el precio va más allá, se
   considera ruptura, no manipulación.

`Profundidad máxima = 0,15 × (máximo del rango de referencia − mínimo del rango de referencia)`

Ejemplo: la sesión americana perfora el mínimo de Europa. Europa: máximo 21100, mínimo 21000 → rango 100 pts →
profundidad máxima 15 pts. El precio puede bajar hasta **20985**; si toca 20984,75 o menos, no es manipulación.


### 8.2 Pivotes de la estructura (D1) – 5m

- **Máximo pivote:** vela de 5m cuyo máximo es mayor que el de las **2 velas anteriores y las 2 siguientes**.
- **Mínimo pivote:** vela de 5m cuyo mínimo es menor que el de las 2 velas anteriores y las 2 siguientes.
- El pivote se considera confirmado recién cuando **cierran las 2 velas siguientes** (no se usa información futura).
- **Estructura alcista válida** mientras ninguna vela cierre por debajo del último mínimo más alto (L2).
  **Estructura bajista válida** mientras ninguna vela cierre por encima del último máximo más bajo.

### 8.3 Invalidación de un rango activo (D2)

Aplica **solo a los rangos de velas** del modelo A-B-C (sección 1.3), no a los niveles de sesión, de la semana
anterior ni del lunes.

Un rango activo queda invalidado si ocurre **cualquiera** de estas dos cosas:

1. Una vela **de la misma temporalidad** cierra más allá del extremo de la barrida de B
   (ej. se activó el extremo inferior de A → una vela cierra por debajo de `B.low`).
2. Pasan **N velas** de esa temporalidad sin alcanzar el objetivo:

   | Temporalidad | N velas |
   |---|---|
   | Diario | 5 |
   | 4h | 6 |
   | 60m | 8 |

### 8.4 Volumen en el giro (D4)

La vela de reingreso tiene **subida de volumen** si su volumen es **≥ 1,5 veces** el volumen promedio de las velas de
5m de **ese mismo horario** en los **últimos 20 días** de sesión (volumen relativo).

### 8.5 Noticias de alto impacto (D5)

No se opera desde **5 minutos antes** hasta **15 minutos después** de una noticia de alto impacto.

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
| 2026-11-20 | P17c: stop de 75 ticks (4 micros) o 150 ticks (2 micros) según volatilidad, siempre 150 USD de riesgo. P17d: si el stop no cubre el pivote, no se toma el trade. |
| 2026-11-20 | P17c/P17e: tercer tamaño de stop, 300 ticks con 1 micro. Elección por ATR: <100 → 75 ticks, 100–200 → 150 ticks, >200 → 300 ticks. |
| 2026-11-20 | P17g: ATR(14) de 60m, en puntos. P17f: si el stop que corresponde por ATR no cubre el pivote, se descarta el trade. |
| 2026-11-20 | P21b: prueba 3.000 USD de beneficio, 2.500 trailing, 1.000 pérdida diaria. P24b: solo noticias de alto impacto. |
| 2026-11-20 | P6: estado semanal = información para la hipótesis. P7b: manipulación se lee en 60m, se opera en 5m. P8: mandan los niveles del lunes. P10b: siguiente objetivo = el que esté primero. |
| 2026-11-20 | P5: la invalidación de rangos activos queda discrecional, sin regla objetiva. Plan cerrado en v1.0. |
| 2026-11-20 | Manipulación válida (validación automática): máximo 2 perforaciones del nivel y profundidad máxima del 15% del rango de la sesión del nivel. |
| 2026-11-20 | V1: perforaciones separadas por al menos una vela de la temporalidad de lectura cerrando dentro del nivel (5m sesiones, 60m semana/lunes). V2: la regla de manipulación aplica también a niveles semanales y del lunes. |
| 2026-11-20 | D1: pivote = 2 velas a cada lado en 5m. D2: invalidación de rangos de velas por cierre más allá de la barrida de B o N velas (D 5, 4h 6, 60m 8). D4: volumen relativo ≥ 1,5× mismo horario últimos 20 días. D5: sin operar de −5 a +15 min de noticias de alto impacto. |
