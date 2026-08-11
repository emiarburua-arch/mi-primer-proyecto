# Correcciones al CL Beta plan 30d

**La lógica de entrada no se toca.** El contexto M60, el trazado de niveles, las
hipótesis A y B, los set ups y el disparador quedan exactamente como están: los datos
dicen que funcionan, porque el winrate se mantuvo estable en el 35–36 % durante los ocho
meses completos.

Lo que se corrige es **la geometría de la operación**: qué relación mínima tiene que
haber entre el stop y el target para que valga la pena entrar.

---

## C1 · Ratio mínimo 2:1 verificado antes de entrar — *la corrección principal*

**Qué dice hoy el plan:** «*los pivotes dinámicos son utilizados como objetivos, por lo
tanto, para tomar una operación el pivote tiene que permitir el recorrido hasta el
target*». La idea correcta ya está escrita, pero **sin número**, y por eso no filtra nada.

**Qué pasa a decir:**

```
Antes de mandar la orden limitada, con el stop ya definido:

    distancia al pivote objetivo  ÷  distancia al stop  ≥  2,0

Si el cociente da menos de 2,0 → la operación NO se toma.
No se acerca el stop para que el número dé. No se estira el target
hasta un pivote que no corresponde. Se descarta y se espera la siguiente.
```

**Por qué éste es el número.** Con el winrate real medido (36 %), la esperanza por
operación a $155 de riesgo es:

| R | 33 % | **36 %** | 40 % | 45 % |
|---:|---:|---:|---:|---:|
| 1,10 | −$48 | **−$38** | −$25 | −$9 |
| 1,51 *(tu R actual)* | −$27 | **−$15** | +$1 | +$20 |
| 1,75 | −$14 | **−$2** | +$16 | +$37 |
| **2,00** | −$2 | **+$12** | +$31 | +$54 |
| 2,25 | +$11 | **+$26** | +$46 | +$72 |

Con tu winrate, el equilibrio está en R = 1,78. Un mínimo de 2,00 deja margen para que
el winrate baje unos puntos sin que el sistema se dé vuelta. Un mínimo de 1,75 sería
operar sobre la línea, y ya sabés lo que pasa cuando el R se desliza por debajo.

Esta regla sola habría eliminado las operaciones de mayo y junio con ratio 0,52 y 0,82,
que son perdedoras por aritmética antes de entrar.

---

## C2 · Cuando sube la volatilidad, el target escala igual que el stop

**El problema medido:** al pasar a MCL el stop se ensanchó 4,7× (15 → 70 ticks por
contrato) y el target sólo 2,75× (30 → 82,5). El plan manda ensanchar el stop con el
ATR pero deja el target anclado a pivotes, que no se mueven con la volatilidad.

**Qué pasa a decir:**

```
Al operar MCL por ATR > 0,6, el objetivo tiene que ser un pivote
que esté como mínimo al doble de la distancia del stop ensanchado.

Si el único pivote disponible es el mismo que usarías en régimen normal
—es decir, si el mercado se volvió más volátil pero el objetivo no se alejó—
ese día no hay operación. No se opera "igual pero con micros".
```

**Lo que esto NO significa:** no es «no operar MCL». El winrate en MCL fue del 38,5 %,
**mejor** que el 33,3 % de CL: en días volátiles leés el mercado igual de bien o mejor.
Prohibir MCL sería tratar el síntoma y te dejaría sin operar meses enteros. Lo que hay
que descartar no son los días volátiles, son las operaciones mal proporcionadas.

En la práctica, en un régimen de ATR alto vas a operar **bastante menos días**, y eso es
correcto: son días en los que el recorrido disponible no paga el riesgo que hay que
asumir.

---

## C3 · Nada de entradas en los primeros 30 minutos

**El dato:** 13 operaciones en la primera media hora tras la apertura cash, **1 sola
ganadora** (7,7 %), −$1.447,52 — más que la pérdida total del sistema. Fisher p = 0,029.

**Qué pasa a decir:**

```
La ventana operativa abre a los 30 minutos de la apertura cash.
Los primeros 30 minutos son de observación: se marcan niveles,
se confirma o descarta la hipótesis, no se opera.
```

Tiene sentido mecánico además del estadístico: el algoritmo necesita estructura formada
para aplicarse, y en los primeros minutos todavía no la hay. Recordá que la apertura se
mueve entre las 10:00 y las 11:00 de Buenos Aires según el horario de EE.UU. — hay que
recalcularla en noviembre y en marzo.

---

## C4 · Giro+FV suspendido; Giro+VC con exigencia mayor

**Los datos:** Giro+FV son 6 operaciones, **0 ganadoras**, −$945,64. Giro+VC son 30
operaciones con 36,7 % de acierto —igual que ESTRUC+VC— pero con R de 1,29 contra 1,57,
y por eso profit factor de 0,75 contra 0,90.

**Qué pasa a decir:**

```
Giro+FV: suspendido. Se sigue anotando como señal observada, sin operar.
Giro+VC: se toma sólo con ratio ≥ 2,5 (no 2,0).
```

**Cuidado con esto:** Giro+FV con 6 operaciones no es estadísticamente concluyente
(p = 0,086), y la familia Giro completa tampoco (p = 0,512). No estoy diciendo que el
Giro no sirva. Lo que sí está medido es que **deja menos recorrido hasta el objetivo**,
porque entra contra el movimiento previo, y eso es exactamente el problema que ataca C1.
La exigencia extra de ratio es la forma de mantenerlo vivo sin que siga drenando.

---

## C5 · Tope de riesgo del 2 % que no se negocia

**El dato:** 10 de 62 perdedoras superaron el 2 % del capital. La peor llegó al 3,52 %
(−$360,20, MCL 5 contratos) y está marcada como indisciplinada. Las 4 operaciones fuera
de plan del año suman −$776, la mitad de la pérdida neta.

**Qué pasa a decir:**

```
El número de contratos se calcula ANTES de entrar, dividiendo
el 2 % del capital por la distancia al stop. Si el resultado no
es un número entero de contratos, se redondea hacia abajo.
Nunca hacia arriba.
```

---

## C6 · Registrar MFE y MAE

Siguen vacíos en 96 de 97 operaciones. En este análisis se pudo reconstruir el R
*realizado* a partir de los ticks de salida, y con eso alcanzó para el diagnóstico. Pero
para elegir bien el target hace falta el R *disponible*: si el precio llegó a rozar el
objetivo y volvió, o si nunca se acercó.

Concretamente, en 30 operaciones más te va a decir si el mínimo de 2,0 de C1 es el
número correcto o si el mercado te da margen para exigir 2,5.

---

## C7 · Respetar el tope semanal de $500

Se superó en 2 de 32 semanas (−$506 y −$958). No es sistemático, pero la semana de
−$958 es casi el doble del límite y por sí sola vale dos tercios de la pérdida anual.
Con el tope respetado, esa semana habría cerrado en −$500.

---

## Resumen

| # | Corrección | Base | Confianza |
|---|---|---|---|
| C1 | Ratio mínimo 2:1 antes de entrar | Aritmética de la esperanza + R medido | **Alta** |
| C2 | El target escala con el stop | Stop 4,7× vs target 2,75× al pasar a MCL | **Alta** |
| C3 | Ventana abre a los 30 min | 13 ops, 1 ganadora, p=0,029 | **Alta** |
| C4 | Giro+FV fuera, Giro+VC con ratio 2,5 | R 1,29 vs 1,57 con igual winrate | Media |
| C5 | Tope 2 % calculado antes de entrar | 10 ops lo superaron | **Alta** |
| C6 | Registrar MFE/MAE | 96 de 97 vacías | **Alta** |
| C7 | Tope semanal $500 | 2 semanas lo superaron | Media |

---

## Honestidad sobre lo que estas correcciones prueban y lo que no

Aplicadas hacia atrás sobre las mismas 97 operaciones, C1+C3+C4 dan 39 operaciones,
41 % de winrate, R 1,90 y **+$1.122** en lugar de −$1.549. Ese número **no es una
predicción y no hay que creérselo**: filtrar hacia atrás los grupos que perdieron
siempre mejora el resultado. Es la trampa clásica de este tipo de análisis.

La validación limpia —fijar las reglas con la primera mitad y medirlas en la segunda—
deja sólo 8 operaciones en la segunda mitad, con profit factor 0,36. **Ocho operaciones
no prueban nada, ni a favor ni en contra.**

Por eso el argumento que sostiene C1 y C2 no es el filtrado histórico, sino la
aritmética: con un 36 % de acierto necesitás R ≥ 1,78, y eso es cierto
independientemente de qué operaciones hayas tomado. Lo que el histórico aporta es la
medición de que tu R real fue 1,51 y de dónde se perdió: del stop que escala con la
volatilidad mientras el target se queda quieto.

**La predicción concreta y falsable** es ésta: si el winrate se mantiene en el 35–36 %
—como se mantuvo durante ocho meses— y el R sube de 1,51 a 2,0 o más, la esperanza pasa
de −$15 a +$12 por operación. Si tras 40 operaciones bajo las reglas nuevas el R medido
no llega a 1,9, o el winrate cae por debajo del 33 %, la hipótesis está mal y hay que
volver sobre la entrada, no sobre la gestión.

Un punto que conviene tener presente: exigir 2:1 va a hacer que **descartes bastantes
más operaciones de las que venías tomando**, sobre todo en días volátiles. Menos
operaciones se siente como estar perdiendo oportunidades, y la tentación va a ser
aflojar el ratio. Ese aflojamiento es exactamente lo que produjo la segunda mitad del año.
