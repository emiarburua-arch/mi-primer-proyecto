# Trading Plan – Micro E-mini Nasdaq-100 (MNQ)

> Estado: **BORRADOR v0.2** – en definición. No se testea nada hasta cerrar todos los `PENDIENTE`.
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
| `B.close > A.high` | Alcista (continuación) | `PENDIENTE P1` |
| `B.close < A.low` | Bajista (continuación) | `PENDIENTE P1` |

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
- `PENDIENTE P5b` – ¿Los rangos activos **caducan** después de cierto tiempo / número de velas, o quedan activos indefinidamente?
- `PENDIENTE P5c` – Si hay rangos activos con **objetivos en direcciones opuestas**, ¿cuál tiene prioridad? (ej. el de mayor temporalidad, el más reciente, el objetivo más cercano).

### 1.4 Casos sin definir

- `PENDIENTE P2` – B cierra dentro de A **sin** haber perforado ningún extremo (inside bar).
- `PENDIENTE P3` – B perfora **ambos** extremos de A y cierra dentro (outside bar): ¿activa los dos rangos, ninguno, o el último perforado?

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

- `PENDIENTE P7` – Definición exacta de "manipular": ¿perfora el nivel y una vela de 60m cierra de vuelta dentro? ¿Otra temporalidad? ¿En cuántas velas máximo debe volver?
- `PENDIENTE P8` – ¿Si PWH/PWL y MH/ML dan lecturas opuestas, cuál manda?

---

## 3. Narrativa multi-temporalidad

Orden de lectura: **Semanal → Diario → 4h → 60m → 5m (ejecución)**.

- `PENDIENTE P9` – Regla de combinación. Propuesta a validar:
  - La temporalidad mayor con sesgo activo define la **dirección y el objetivo** de la narrativa.
  - Las temporalidades menores se usan para encontrar el **momento**: se opera cuando su modelo A-B-C apunta en la
    dirección del objetivo mayor.
  - Si una temporalidad menor contradice a la mayor → ¿se espera, se opera igual, o se cambia de dirección?
- `PENDIENTE P10` – ¿Qué pasa cuando la temporalidad mayor ya alcanzó su objetivo? (ej. diario reversión alcista ya tocó `A.high`).

---

## 4. Niveles de sesión (en 5m)

| Sesión | Horario (ET) – `PENDIENTE P11` confirmar |
|---|---|
| Asia | 18:00 – 03:00 |
| Europa | 03:00 – 08:00 |
| América | 09:30 – 16:00 |

Se marcan máximo y mínimo de cada sesión.

---

## 5. Gatillos de entrada (5m)

### 5.1 Entrada tipo 1 – Barrida de sesión

Con sesgo/narrativa **alcista**:
1. El precio barre el **mínimo de la sesión Asia o Europa**.
2. Aparece una **vela de confirmación** (ver 5.3).
3. Entrada → `PENDIENTE P12` (cierre de la vela de confirmación, o ruptura de su máximo, u orden límite).

Bajista: inverso (barrida del máximo de Asia o Europa).

### 5.2 Entrada tipo 2 – Retroceso en continuación

Con la continuación ya iniciada en dirección deseada:
1. Se espera un **retroceso**. `PENDIENTE P13` – definir retroceso (ej. ¿N velas contrarias?, ¿hasta qué nivel?: 50% del impulso, nivel de sesión, mitad de la vela anterior…).
2. Se espera una **nueva vela en dirección deseada**.
3. Se espera la **vela de confirmación** (5.3).
4. Entrada → igual que P12.
- `PENDIENTE P14` – ¿Cómo se define "continuación comenzada"? (ej. ya hubo entrada tipo 1, o rompió un máximo de sesión, etc.).

### 5.3 Vela de confirmación

`PENDIENTE P15` – Definición exacta. Opciones típicas:
- Vela que cierra a favor (alcista: `close > open`).
- Vela que cierra por encima del máximo de la vela anterior (aplicando el mismo modelo A-B-C en 5m).
- Vela que cierra de vuelta dentro del rango de sesión barrido.
- Tamaño mínimo de cuerpo (% del rango de la vela).

### 5.4 Ventana horaria de ejecución

`PENDIENTE P16` – ¿En qué horario se buscan entradas? (ej. solo 09:30–11:30, toda la sesión americana, también Londres).

---

## 6. Gestión del trade

- **Stop loss** – `PENDIENTE P17` (ej. debajo de la mecha de la barrida ± N ticks, debajo de la vela de confirmación).
- **Take profit** – `PENDIENTE P18` (ej. siguiente nivel de la narrativa: extremo opuesto de sesión, de A, del lunes o de la semana; ¿R mínimo exigido para tomar el trade?).
- **Break-even / parciales** – `PENDIENTE P19`.
- **Salida por tiempo** – `PENDIENTE P20` (ej. cerrar todo a las 15:55).

---

## 7. Gestión de riesgo

- `PENDIENTE P21` – Capital de la cuenta.
- `PENDIENTE P22` – Riesgo por trade (en $ o % de cuenta) y número de contratos.
- `PENDIENTE P23` – Máximo de trades por día y pérdida diaria máxima.
- `PENDIENTE P24` – Días / eventos que no se operan (FOMC, CPI, NFP, festivos, etc.).

---

## Registro de decisiones

| Fecha | Decisión |
|---|---|
| 2026-11-18 | Sesgo por modelo de velas A-B-C (continuación si B cierra fuera de A; reversión si B activa un extremo de A y cierra dentro, objetivo el extremo opuesto). |
| 2026-11-18 | Las temporalidades no necesitan estar alineadas: se lee una narrativa. |
| 2026-11-18 | Niveles semanales (PWH/PWL) y del lunes (MH/ML) se usan para ubicar el precio y detectar manipulación de un extremo → objetivo el extremo opuesto. |
| 2026-11-19 | P4 cerrado: activar un rango = B perfora un extremo de A, vuelve a ingresar y cierra dentro de A; objetivo = extremo contrario de A. |
| 2026-11-19 | Los rangos activados quedan activos aunque C no llegue al objetivo; pueden convivir varios rangos activos. |
| 2026-11-19 | P5: la invalidación de un rango activo es discrecional (el mercado continuó sin darle importancia). Se registra en el diario; queda pendiente una regla objetiva que la aproxime. |
| 2026-11-18 | Entradas en 5m: barrida de máx/mín de Asia o Europa + vela de confirmación; o retroceso en continuación + vela en dirección + confirmación. |
