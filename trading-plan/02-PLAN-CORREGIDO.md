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

| Escenario | ATR M60 | Instrumento | Stop | Contratos | Riesgo | Target 2,5:1 | Gana | Pierde | R neto |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| **A** | bajo | CL | 15 tk | 1 | $150 | 38 tk | +$374,68 | −$155,32 | **2,41** |
| **B** | medio | MCL | 30 tk | 5 | $150 | 75 tk | +$365,80 | −$159,20 | **2,30** |
| **C** | alto | MCL | 50 tk | 3 | $150 | 125 tk | +$369,48 | −$155,52 | **2,38** |
| **D** | muy alto | MCL | 75 tk | 2 | $150 | 188 tk | +$372,32 | −$153,68 | **2,42** |

Los números salen redondos por casualidad afortunada: 15 × $10 = 30 × $1 × 5 = 50 × $1 ×
3 = 75 × $1 × 2 = $150 exactos en los cuatro casos. El escenario D es opcional; con tres
alcanza si preferís no operar los días de volatilidad extrema.

**Los umbrales de ATR hay que fijarlos con tus propios registros**, no a ojo: tomá el ATR
que anotás en la preparación de sesión, ordenalo, y partí la distribución en tercios. Lo
importante no es dónde caiga exactamente cada corte, sino que el riesgo en dólares no se
mueva al pasar de un escenario a otro.

---

## C2 · El ratio pasa de 2:1 a 2,5:1

**Por qué no alcanza con 2:1.** Después de comisiones, un 2:1 bruto deja un R neto de
1,83–1,93 y un winrate de equilibrio del 34,2–35,4 %. Con tu 35,4 % medido, el margen es
de **medio punto**. Eso es operar sobre la línea: cualquier racha mala y volvés a estar en
rojo.

| Ratio bruto | R neto | Equilibrio | Tu margen | Esperanza/op | En 96 ops |
|---|---:|---:|---:|---:|---:|
| 2,0 : 1 | ~1,87 | 34,8 % | **+0,6 pts** | +$2,48 | +$238 |
| **2,5 : 1** | **~2,35** | **29,9 %** | **+5,5 pts** | **+$28,81** | **+$2.766** |

El salto de 2:1 a 2,5:1 es la diferencia entre depender de que el winrate no baje ni un
punto y tener colchón para una mala racha. Con 2,5:1 podés caer al 30 % de acierto y
seguir en equilibrio.

**El coste:** con un objetivo más lejos vas a convertir menos operaciones. Si al medirlo
el winrate cae por debajo del 30 %, el 2,5:1 no compensa y hay que volver al 2:1 con
escenarios más estrechos. Eso se decide con datos, a las 40 operaciones — no antes.

---

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

Siguen vacíos en 96 de las 97 operaciones. Con el stop ya fijo por escenario, el MFE pasa
a responder la pregunta que importa para C2: **¿cuántas de las perdedoras llegaron a
tocar 2R antes de girarse?** Si son muchas, el 2,5:1 es alcanzable y conviene. Si casi
ninguna llega a 2R, hay que volver al 2:1.

Sin ese dato, la elección entre 2:1 y 2,5:1 se decide sólo por el resultado agregado, que
tarda meses. Con él, se decide en 30 operaciones.

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
| C2 | Ratio 2,5:1 en vez de 2:1 | Aritmética de comisiones y margen | **Alta** |
| C3 | Nada se cierra por debajo de 1R | 4 de 34 ganadoras aportaron $69 | **Alta** |
| C4 | Ventana desde el minuto 30 | 13 ops, 1 ganadora, p=0,029 | **Alta** |
| C5 | Giro+FV suspendido y en observación | 0 de 6, p=0,086 | Media |
| C6 | Registrar MFE/MAE | 96 de 97 vacías | **Alta** |
| C7 | Topes de sesión y semana | 2 días y 2 semanas fuera | Media |

---

## Qué esperar, honestamente

Aplicando sólo C1 y C2 sobre la **misma secuencia de aciertos y fallos del año pasado**
—34 ganadoras y 62 perdedoras, sin suponer ninguna mejora en la lectura del mercado:

| Escenario | Resultado |
|---|---:|
| Ideal: toda ganadora cobra 2R, toda perdedora pierde 1R | +$900 |
| Con deslizamiento (ganadora 1,9R) | +$390 |
| Con deslizamiento y stop real 1,05R | −$44 |
| Manteniendo las 4 ganadoras que no cobraron | −$220 |
| **Lo que pasó en realidad** | **−$1.549** |

Con ratio 2:1 el rango honesto va de **−$220 a +$900**: es decir, C1 sola convierte un año
malo en un año plano. **Por eso hace falta C2 y C3.** Con 2,5:1 y sin ganadoras
desperdiciadas, la esperanza sube a unos +$29 por operación, pero ese número depende de
que el winrate aguante el objetivo más lejano, y eso todavía no está medido.

**La predicción falsable:** si el winrate se mantiene en el 33–36 % con el objetivo a
2,5:1, el sistema pasa a positivo. Si al llevar el objetivo más lejos el winrate cae por
debajo del 30 %, el 2,5:1 no compensa y hay que volver a 2:1 — donde el margen es medio
punto y entonces el trabajo pasa a ser subir el acierto, no la geometría.

**Lo que sí es seguro:** igualar el riesgo en dólares entre escenarios no tiene
contrapartida. No reduce el número de operaciones, no exige acertar más y no depende de
ninguna hipótesis sobre el mercado. Es aritmética: recupera 0,44 puntos de R que se
estaban perdiendo por dimensionamiento.
