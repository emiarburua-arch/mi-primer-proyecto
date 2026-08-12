# CL Beta plan 30d — diagnóstico sobre 97 operaciones reales

Fuente única: `B20x50 - CL Beta plan 30d 22-10.xlsx` (97 operaciones, cuenta real,
22/10/2025 → 26/06/2026) y `Trading Plan Personal.docx` (reglas vigentes).

Una operación (la n.º 96) tiene la fecha corrupta —figura como `1900-01-25` y lleva la
nota «cant de cont mal»— y queda fuera de los cortes temporales. Los totales globales
la incluyen; su efecto es +$134.

---

## 1. El resultado

| | |
|---|---:|
| Capital inicial | $10.000 |
| Capital final | **$8.584,52** |
| P&L neto | **−$1.415,48 (−14,15 %)** |
| Operaciones | 97 en 79 días operados |
| Winrate | **36,1 %** (35 ganadoras / 62 perdedoras) |
| Ganancia media | $235,52 |
| Pérdida media | −$155,79 |
| **R real** (gan. media / pérd. media) | **1,51** |
| **Winrate de equilibrio** que exige ese R | **39,8 %** |
| Profit factor | **0,853** |
| Esperanza por operación | −$14,59 |
| Máximo drawdown | −$2.321 (23 % de la cuenta) |
| Racha máxima de perdedoras | 10 |

**Faltan 3,7 puntos de winrate.** O, dicho al revés, con el winrate que ya tenés hace
falta un R de 1,78 en lugar de 1,51. El sistema no está lejos: está justo del lado
equivocado de la línea.

---

## 2. El hallazgo central: el winrate no se movió, el R se derrumbó

Partiendo la muestra en dos mitades iguales de 48 operaciones:

| | 1.ª mitad (22 oct – 15 ene) | 2.ª mitad (16 ene – 26 jun) |
|---|---:|---:|
| Operaciones | 48 | 48 |
| **Winrate** | **35,4 %** | **35,4 %** |
| Ganancia media | $292,33 | $184,68 |
| Pérdida media | −$143,38 | −$168,19 |
| **R** | **2,04** | **1,10** |
| Winrate de equilibrio | 32,9 % | 47,7 % |
| **P&L** | **+$524,64** | **−$2.074,16** |
| Instrumento | 48 CL / 0 MCL | 9 CL / **39 MCL** |
| Contratos medios | 1,00 | 2,10 |

El winrate es **idéntico al decimal** en las dos mitades. La lectura del mercado, la
selección de setups y la ejecución producen exactamente la misma tasa de acierto de
principio a fin. Lo único que cambió es la geometría de las operaciones: el R pasó de
2,04 a 1,10, y con eso el umbral de equilibrio saltó del 32,9 % al 47,7 %.

Con un 35,4 % de acierto, un R de 2,04 da beneficio y un R de 1,10 es ruinoso. Es el
mismo trader, el mismo método y el mismo acierto a los dos lados de la tabla.

---

## 3. Por qué se derrumbó el R: se arriesgó más en las operaciones que salieron mal

**El ratio 2:1 se respetó.** Las ganadoras en CL se agrupan exactamente en el doble de su
stop: con stop de 15 ticks salen a 30, con stop de 10 salen a 20, con stop de 12 salen a
24. El plan se ejecutó como estaba escrito, operación por operación.

Lo que no se mantuvo constante fue **cuántos dólares había detrás de cada operación**:

| | Riesgo medio cuando **ganaste** | Riesgo medio cuando **perdiste** | Diferencia |
|---|---:|---:|---:|
| CL | $142,89 | $146,90 | 1,03× |
| **MCL** | **$94,70** | **$169,86** | **1,79×** |
| **Todas** | **$121,63** | **$155,79** | **1,28×** |

Ahí está todo el problema, y es puramente aritmético:

```
ganancia media = 2 × $121,63 = $243,26
pérdida media  =              $155,79
R realizado    = 243,26 / 155,79 = 1,56
```

El R medido en la planilla es **1,53**. La cuenta da 1,56. **La diferencia entre el 2,00
que planificabas y el 1,53 que cobraste se explica entera por haber arriesgado un 28 %
más de dólares en las operaciones que salieron mal**, sin que ninguna operación
individual haya incumplido el 2:1.

No hace falta ningún otro factor para explicar la pérdida del año.

### Por qué pasó: la dispersión del stop

El stop se elegía operación por operación, según lo que hiciera falta para proteger el
pivote de ese día. En ticks por contrato:

| | Mínimo | p25 | Mediana | p75 | Máximo | Dispersión |
|---|---:|---:|---:|---:|---:|---:|
| CL | 10 tk | 12 | 15 | 16 | 20 tk | 2,0× |
| **MCL** | 11 tk | 60 | 70 | 95 | **200 tk** | **18,2×** |

En CL la dispersión es tolerable y el efecto casi no se nota (1,03×). En MCL el stop más
ancho es **18 veces** el más estrecho, y ahí el sesgo se dispara a 1,79×. Por eso la
segunda mitad del año —donde 39 de 48 operaciones fueron MCL— es la que se lleva la
pérdida.

### Lo que NO explica la pérdida

**Los stops anchos no aciertan menos.** Operaciones con stop mayor a 25 ticks: 32,4 % de
acierto. Con stop menor o igual a 25: 37,1 %. Fisher **p = 0,66**, no significativo. No es
que pedir un stop ancho señale un setup peor — es sólo que cuando lo pediste arriesgaste
más dólares.

Esto es una buena noticia: significa que la corrección es de dimensionamiento, no de
criterio. No hay que dejar de tomar esas operaciones, hay que tomarlas con el tamaño
correcto.

### El segundo agujero: las ganadoras que no cobran

Cuatro operaciones cuentan como ganadoras pero cobraron casi nada:

| Fecha | Instrumento | Cobrado | En R |
|---|---|---:|---:|
| 2026-01-19 | CL 1c | $4,68 | 0,03R |
| 2026-06-16 | MCL 3c | $9,48 | 0,06R |
| 2026-05-15 | MCL 2c | $22,32 | 0,14R |
| 2026-04-15 | MCL 2c | $32,32 | 0,21R |

Con un winrate del 35 %, cada ganadora es un recurso escaso: **son 4 de 34, el 12 % de
las ganadoras del año**, y aportan $69 donde deberían aportar unos $1.200. Corresponden
a la excepción que el plan sí contempla —«*si la operación se demora y debemos dejar la
sesión*»— pero el coste de esa excepción nunca se había medido.

### La misma firma aparece en los set ups

| Set up | Ops | Winrate | R | Equilibrio | PF | P&L |
|---|---:|---:|---:|---:|---:|---:|
| ESTRUC+FV | 8 | 50,0 % | 2,24 | 30,9 % | 2,24 | +$678,00 |
| ESTRUC+VC | 52 | 36,5 % | 1,57 | 38,9 % | 0,90 | −$488,80 |
| Giro+VC | 30 | 36,7 % | 1,29 | 43,7 % | 0,75 | −$793,08 |
| Giro+FV | 6 | 0,0 % | — | — | 0,00 | −$945,64 |

Mirá ESTRUC+VC y Giro+VC: **36,5 % y 36,7 % de acierto, prácticamente el mismo número**.
Lo que los separa es el R (1,57 contra 1,29), y con eso el profit factor cae de 0,90 a
0,75. Es la misma firma que en el resto del análisis: **el acierto no distingue a los set
ups, el R sí**. Con el riesgo por operación igualado, esa diferencia debería reducirse
sola; si después de 40 operaciones el Giro sigue entregando menos R que la estructura,
entonces sí hay algo propio del set up y habrá que tratarlo aparte.

---

## 4. El otro hallazgo con respaldo estadístico: los primeros 30 minutos

Midiendo los minutos desde la apertura cash (ajustado por los cambios de horario de
EE.UU. de noviembre y marzo, que mueven la apertura entre las 10:00 y las 11:00 de
Buenos Aires):

| Ventana | Ops | Winrate | P&L |
|---|---:|---:|---:|
| Antes de la apertura | 5 | 40,0 % | +$63,40 |
| **0–29 min** | **13** | **7,7 %** | **−$1.447,52** |
| 30–59 min | 33 | 33,3 % | −$579,00 |
| 60–89 min | 24 | 37,5 % | −$228,24 |
| 90–119 min | 14 | 35,7 % | −$122,40 |
| Más de 2 h | 7 | 85,7 % | +$764,24 |

Trece operaciones en la primera media hora, **una sola ganadora**, y una pérdida de
$1.447 que es mayor que la pérdida total del sistema. Test exacto de Fisher: **p =
0,029**, significativo. Tiene además una explicación mecánica evidente: en los primeros
minutos no hay estructura formada sobre la que aplicar el algoritmo, y el ruido de la
apertura toca cualquier stop.

El extremo opuesto (más de 2 h, 85,7 % de acierto, p = 0,007) también sale significativo,
pero son 7 operaciones y conviene tratarlo como una pista, no como una regla.

---

## 5. Qué NO resistió el análisis

Esto importa tanto como lo anterior, porque son los cortes que a simple vista parecen
culpables y no lo son. Test exacto de Fisher sobre el winrate:

| Corte | Ops | Winrate | P&L | p | ¿Significativo? |
|---|---:|---:|---:|---:|---|
| Primeros 30 min | 13 | 7,7 % | −$1.447,52 | 0,029 | **sí** |
| Más de 2 h | 7 | 85,7 % | +$764,24 | 0,007 | **sí** |
| Giro+FV | 6 | 0,0 % | −$945,64 | 0,086 | no (marginal) |
| Familia Giro | 36 | 30,6 % | −$1.738,72 | 0,512 | no |
| Operaciones en corto | 32 | 28,1 % | −$1.432,60 | 0,367 | no |
| Instrumento MCL | 39 | 38,5 % | −$1.296,28 | 0,667 | no |
| Lunes | 11 | 18,2 % | −$1.098,52 | 0,318 | no |
| Con salidas parciales | 35 | 40,0 % | −$937,40 | 0,512 | no |

Tres conclusiones que van contra la intuición:

**Los cortos no son el problema.** Pierden $1.432, pero su winrate (28,1 %) no se separa
del resto de forma significativa. La diferencia es ruido más un régimen de mercado
concreto; prohibirlos sería ajustar la regla a lo que ya pasó.

**MCL tampoco es el problema en sí.** Su winrate es del 38,5 %, **mejor** que el 33,3 % de
CL. Las entradas en días volátiles se leen igual de bien o mejor. Lo que falla es el R
con el que se toman. Prohibir MCL sería tratar el síntoma: en marzo, abril y mayo de 2026
te habría dejado sin operar un solo día.

**Los lunes tampoco.** Once operaciones no dicen nada, por mal que se vean.

---

## 6. Cumplimiento de las reglas del plan

| Regla del plan | Cumplimiento |
|---|---|
| Máximo 2 operaciones por día | 2 días con 3 operaciones (31/10 y 14/11) |
| Máxima pérdida semanal $500 | Superada en 2 de 32 semanas (W49-2025: −$506; W15-2026: −$958) |
| Riesgo 1 %–2 % | **10 de 62 perdedoras superaron el 2 %**; la peor, 3,52 % |
| Operación disciplinada | 92 de 96; las 4 indisciplinadas suman −$776 (media −$194) |

La disciplina general es buena y las desviaciones son puntuales, pero las que hay son
caras: cuatro operaciones fuera de plan se llevaron la mitad de la pérdida neta del año.
La peor operación de toda la muestra (−$360,20, MCL 5 contratos, 3,52 % de la cuenta)
está marcada como indisciplinada.

---

## 7. Lo que sigue sin registrarse

**MFE y MAE están vacíos en 96 de las 97 operaciones.** Son las columnas que dirían
cuánto recorrido a favor tuvo cada perdedora antes de girarse y cuánto respiro necesitó
cada ganadora.

En este análisis se pudo reconstruir el R *realizado* a partir de los ticks de salida,
que es lo que permitió llegar al diagnóstico. Pero para calibrar el target hace falta el
R *disponible*: saber si el precio llegó a rozar el objetivo y volvió, o si nunca se
acercó. Sin eso, la elección del target sigue siendo a ojo.

---

## 8. Resumen

1. El sistema pierde por **3,7 puntos de winrate**, o equivalentemente por 0,27 puntos
   de R. Está cerca del equilibrio, no lejos.
2. **El winrate es estable en el 35–36 % durante los ocho meses.** La lectura de mercado
   no se degradó.
3. Lo que se rompió es el **R: de 2,04 a 1,10**, cuando la operativa pasó a MCL.
4. La causa está medida y es aritmética: **el ratio 2:1 se respetó siempre, pero se
   arriesgaron un 28 % más de dólares en las operaciones que salieron mal** ($155,79
   contra $121,63). Eso solo lleva el R de 2,00 a 1,56, y el medido es 1,53.
5. El origen es la **dispersión del stop**: en MCL el más ancho es 18 veces el más
   estrecho, y el tamaño de la posición no compensó esa variación.
6. Los **primeros 30 minutos** son el único corte horario con respaldo estadístico:
   13 operaciones, 1 ganadora, −$1.447.
7. Los cortos, MCL y los lunes **no** resisten el test: son ruido, no causas.

Las correcciones están en `02-PLAN-CORREGIDO.md`.
