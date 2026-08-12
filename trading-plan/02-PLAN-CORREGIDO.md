# Correcciones al CL Beta plan 30d

**La lógica de entrada no se toca.** El contexto M60, el trazado de niveles, las
hipótesis A y B, los set ups y el disparador quedan exactamente como están: el winrate se
mantuvo estable en el 35–36 % durante los ocho meses completos, así que esa parte
funciona.

**El ratio 2:1 tampoco se toca en su espíritu** — se respetó operación por operación. Lo
que se corrige es el **tamaño de la posición**, que es donde se fue el resultado del año.

---

## C1 · Tres escenarios de stop fijo, con el mismo riesgo en dólares — *la corrección principal*

**El problema medido:** arriesgaste $121,63 de media en las operaciones que ganaste y
$155,79 en las que perdiste — un 28 % más. Eso solo, sin incumplir el 2:1 ni una vez,
lleva el R de 2,00 a 1,56 (el medido fue 1,53). En MCL el sesgo llega a 1,79×, porque el
stop más ancho que usaste fue **18 veces** el más estrecho.

**Qué pasa a decir:** el stop deja de elegirse operación por operación y pasa a ser uno de
tres (o cuatro) valores fijos según el ATR, cada uno con su número de contratos ya
calculado para que **el riesgo en dólares sea siempre el mismo**.

| Escenario | ATR M60 | Instrumento | Stop | Contratos | Riesgo | Target 2:1 | Gana | Pierde | R neto |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| **A** | bajo | CL | 15 tk | 1 | $150 | 30 tk | +$294,68 | −$155,32 | **1,90** |
| **B** | medio | MCL | 30 tk | 5 | $150 | 60 tk | +$290,80 | −$159,20 | **1,83** |
| **C** | alto | MCL | 50 tk | 3 | $150 | 100 tk | +$294,48 | −$155,52 | **1,89** |
| **D** | muy alto | MCL | 75 tk | 2 | $150 | 150 tk | +$296,32 | −$153,68 | **1,93** |

Fijate en el escenario B: cinco micros pagan $9,20 de comisión contra los $5,52 de tres,
para el mismo riesgo. Cuando dos escenarios sirvan para el mismo ATR, **elegí siempre el
que use menos contratos** — el R neto sube de 1,83 a 1,89 sin cambiar nada más.

Los números salen redondos por casualidad afortunada: 15 × $10 = 30 × $1 × 5 = 50 × $1 ×
3 = 75 × $1 × 2 = $150 exactos en los cuatro casos. El escenario D es opcional; con tres
alcanza si preferís no operar los días de volatilidad extrema.

**Los umbrales de ATR hay que fijarlos con tus propios registros**, no a ojo: tomá el ATR
que anotás en la preparación de sesión, ordenalo, y partí la distribución en tercios. Lo
importante no es dónde caiga exactamente cada corte, sino que el riesgo en dólares no se
mueva al pasar de un escenario a otro.

---

## C2 · El ratio se queda en 2:1 — *comprobado con las capturas*

En una versión anterior de este documento recomendé subir el objetivo a 2,5:1, razonando
que después de comisiones el 2:1 deja apenas medio punto de margen sobre el winrate de
equilibrio. **Las capturas de las sesiones de 2026 desmienten esa recomendación y queda
retirada.**

### La medición

Sobre las ganadoras con captura se puede leer hasta dónde llegó el precio después de
tocar el objetivo, midiendo la excursión máxima en múltiplos de R:

| Fecha | Instrumento | Stop / Target | Máximo alcanzado |
|---|---|---|---:|
| 2026-03-20 | MCL 2c | 91 / 182 tk | **2,11 R** |
| 2026-04-23 | MCL 2c | 105 / 210 tk | **2,28 R** |
| 2026-04-29 | MCL 2c | 93 / 187 tk | **2,42 R** |
| 2026-04-16 | MCL 2c | 58 / 116 tk | **3,05 R** |

De cuatro ganadoras, **una sola habría alcanzado un objetivo puesto a 2,5R**. Las otras
tres se habrían dado vuelta antes de llegar y, en lugar de cobrar 2R, habrían recorrido
todo el camino de vuelta hasta el stop.

### Por qué eso es demoledor

Subir el objetivo no es gratis: cada ganadora que no llega al nuevo objetivo no se queda
en cero, **se convierte en una perdedora completa**. El intercambio es +0,5R en las que
llegan contra −3R en las que no.

| % de ganadoras que alcanzan 2,5R | Resultado sobre el mismo año |
|---:|---:|
| 25 % *(lo medido: 1 de 4)* | **−$9.938** |
| 50 % | −$5.475 |
| 70 % | −$1.905 |
| **80,7 %** | **$0 — punto de equilibrio** |
| 100 % | +$3.450 |

**Haría falta que el 81 % de tus ganadoras llegara a 2,5R.** La muestra dice 25 %. Aunque
cuatro capturas son pocas y el intervalo es ancho, para que el 2,5:1 compensara habría que
estar equivocado por un factor de tres.

### Lo que esto confirma

El objetivo a 2R no está mal puesto: **está puesto donde el precio efectivamente llega**.
Las cuatro ganadoras medidas alcanzaron entre 2,11R y 3,05R — es decir, el 2:1 captura
casi todo el movimiento disponible y el margen por encima es delgado y variable.

El margen sobre el equilibrio, entonces, no se va a conseguir estirando el objetivo. Se
consigue con C1 (que recupera 0,44 puntos de R) y con C4, que es donde está el dinero.

## C3 · Ninguna operación se cierra por debajo de 1R

**El problema medido:** cuatro operaciones cuentan como ganadoras pero cobraron $4,68,
$9,48, $22,32 y $32,32 — entre 0,03R y 0,21R. Son **4 de las 34 ganadoras del año** y
aportan $69 donde deberían aportar unos $1.200.

Con un winrate del 35 %, cada ganadora es un recurso escaso: desperdiciar el 12 % de
ellas es caro. Corresponden a la excepción que el plan ya contempla —«*si la operación se
demora y debemos dejar la sesión*»— pero esa excepción nunca tuvo un límite.

**Qué pasa a decir:**

```
Si al llegar la hora de cerrar la sesión la operación no alcanzó 1R,
no se cierra a mercado: se deja corriendo con el stop original
y el target original, y se registra el resultado al día siguiente.

Si eso no es posible (no podés dejar la posición abierta),
entonces esa operación no se toma. Se descarta antes de entrar,
no se abandona a mitad de camino.
```

La segunda mitad de la regla es la importante: si sabés que a las 12:30 tenés que
levantarte, no abras una operación a las 12:10.

---

## C4 · La ventana operativa abre a los 30 minutos

**El dato:** 13 operaciones en la primera media hora tras la apertura cash, **1 sola
ganadora** (7,7 %), −$1.447,52 — más que la pérdida total del sistema. Fisher **p =
0,029**, el único corte horario que resiste el test.

```
La ventana operativa abre a los 30 minutos de la apertura cash.
Los primeros 30 minutos son de observación: se marcan niveles
y se confirma o descarta la hipótesis, no se opera.
```

Tiene sentido mecánico además del estadístico: el algoritmo necesita estructura formada
para aplicarse. Ojo con la apertura, que se mueve entre las 10:00 y las 11:00 de Buenos
Aires según el horario de EE.UU. — hay que recalcularla en noviembre y en marzo.

---

## C5 · Giro+FV suspendido

6 operaciones, **0 ganadoras**, −$945,64. Con n=6 no es concluyente (p = 0,086), así que
no es una condena: se suspende y se sigue anotando como señal observada sin operar. Si
en 30 sesiones el registro muestra que habría funcionado, vuelve.

Giro+VC (30 operaciones, 36,7 % de acierto, R 1,29) **se mantiene**. Su winrate es idéntico
al de ESTRUC+VC; lo que lo hundía era el R, y C1 ataca justamente eso. Se lo vuelve a
medir a las 40 operaciones.

---

## C6 · Registrar MFE y MAE

Siguen vacíos en 96 de las 97 operaciones. Las capturas permitieron reconstruirlo para
cuatro ganadoras, y con eso alcanzó para descartar el 2,5:1 — pero cuatro son pocas.

El dato que hay que acumular es **hasta dónde llegó el precio en las ganadoras después de
tocar el objetivo**. Si con 20 o 30 medidas resultara que la mayoría supera 2,5R, la
decisión de C2 habría que revisarla. Con cuatro, lo único que se puede decir es que la
evidencia disponible apunta claramente en contra.

En las perdedoras el MFE tiene otro uso: dice si el precio llegó a moverse a favor antes
de girarse o si fue en contra desde el primer momento. Eso es lo que separa un problema
de entrada de un problema de aguante.

*(Nota: preguntar «cuántas perdedoras llegaron a 2R» no tiene sentido — si hubieran
llegado a 2R habrían tocado el objetivo y serían ganadoras. Esa pregunta, que aparecía en
una versión anterior de este documento, era circular.)*

---

## C7 · Topes que no se negocian

| Regla | Estado en la muestra |
|---|---|
| Máximo 2 operaciones por día | 2 días con 3 operaciones |
| Máxima pérdida semanal $500 | Superada en 2 de 32 semanas (−$506 y −$958) |
| Riesgo máximo 2 % | 10 de 62 perdedoras lo superaron; la peor, 3,52 % |

Con los escenarios de C1 el riesgo queda fijado en $150 (1,5 %) por construcción, así que
el tercer punto se resuelve solo. Los otros dos son de ejecución. La semana de −$958 vale
por sí sola dos tercios de la pérdida del año.

---

## Resumen

| # | Corrección | Base | Confianza |
|---|---|---|---|
| C1 | Tres escenarios de stop, riesgo fijo $150 | Explica el R medido con 0,03 de error | **Alta** |
| C2 | El ratio se queda en 2:1 | 4 ganadoras medidas: 2,11–3,05R | **Alta** |
| C3 | Nada se cierra por debajo de 1R | 4 de 34 ganadoras aportaron $69 | **Alta** |
| **C4** | **Ventana desde el minuto 30** | **13 ops, 1 ganadora, p=0,029 — la de mayor impacto** | **Alta** |
| C5 | Giro+FV suspendido y en observación | 0 de 6, p=0,086 | Media |
| C6 | Registrar MFE/MAE | 96 de 97 vacías | **Alta** |
| C7 | Topes de sesión y semana | 2 días y 2 semanas fuera | Media |

---

## Qué esperar, honestamente

Sobre la **misma secuencia de aciertos y fallos del año pasado** —34 ganadoras y 62
perdedoras, sin suponer ninguna mejora en la lectura del mercado— y con riesgo fijo de
$150 y objetivo a 2R:

| | Ganadoras / perdedoras | Neto | En dólares |
|---|---|---:|---:|
| Sólo C1 (riesgo fijo) | 34W / 62L | +6R | **+$900** |
| **C1 + C4 (sin los primeros 30 min)** | **33W / 50L** | **+16R** | **+$2.400** |
| C1 + C4 + C3 (sin las que hay que abandonar) | 29W / 50L | +8R | +$1.200 |
| *Lo que pasó en realidad* | 34W / 62L | | *−$1.549* |

El rango honesto es **+$1.200 a +$2.400**. La diferencia entre las dos últimas filas es
qué se supone que habría pasado con las cuatro operaciones cerradas por debajo de 1R: si
se hubieran dejado correr habrían aportado hasta 2R cada una, y si no se hubieran tomado
no aportan nada. No hay forma de saber cuál de las dos, así que quedan las dos puntas.

Lo llamativo es que **C4 vale más que C1**: descartar trece operaciones de la primera media
hora suma +10R, mientras que igualar el riesgo suma +6R. La corrección más barata del
documento es también la más rentable.

### Lo que es seguro y lo que no

**Seguro:** igualar el riesgo en dólares no tiene contrapartida. No reduce el número de
operaciones, no exige acertar más, no depende de ninguna hipótesis sobre el mercado.
Recupera 0,44 puntos de R que se estaban perdiendo por dimensionamiento.

**Razonablemente firme:** la ventana desde el minuto 30. Trece operaciones con una sola
ganadora, p = 0,029, y una explicación mecánica de por qué debería ser así.

**Todavía abierto:** el margen sobre el equilibrio sigue siendo delgado. Con riesgo fijo y
2:1 neto de comisiones el equilibrio está en el 34,5–35,4 % y tu winrate medido es 35,4 %.
C4 es lo que abre el hueco, al sacar de la muestra un grupo de operaciones con un 7,7 % de
acierto. Si en las próximas 40 operaciones el winrate fuera del grupo de la primera media
hora no se sostiene por encima del 38 %, el sistema vuelve a quedar sobre la línea y el
trabajo pasa a ser subir el acierto — no la geometría, que ya está donde tiene que estar.

### Una observación de las capturas que conviene mirar

En la operación del 08/04 el precio bajó, tocó el stop y **desde ahí se fue directo hasta
la zona del objetivo**. La dirección estaba bien leída; lo que falló fue el momento de
entrar: hubo una perforación del mínimo antes del movimiento bueno.

Es un solo caso y no alcanza para concluir nada, pero es exactamente el fenómeno que el
set up Giro está pensado para aprovechar (esperar la manipulación en vez de anticiparla).
Con el resto de las capturas se puede contar en cuántas perdedoras se repite. Si fueran
muchas, ahí habría una mejora de winrate — que es justo lo que hace falta y lo único que
el ajuste de geometría no puede dar.
