# TPP EA n02 — correcciones al Trading Plan Personal

Versión corregida del `TPP EA n1`. **La lógica de entrada no cambia**: contexto M60,
algoritmo Ankora en M5, elementos primarios (estructura / facilidad) y disparadores
(vela de confirmación / falta de volumen) quedan exactamente como están.

Lo que cambia es dónde se pone el stop, cuánto se arriesga, qué se mide y en qué
cuenta se opera. Son siete correcciones, ordenadas por impacto.

---

## C1 · Registrar MFE y MAE en cada operación — *obligatorio*

**Estado actual:** las columnas existen en la planilla B20x50 y están vacías en las
cuatro planillas, backtest y real.

**Corrección:** ninguna operación se da por cerrada en el registro sin MFE (máximo
recorrido a favor, en ticks) y MAE (máximo recorrido en contra, en ticks).

**Por qué es la primera de la lista:** es el único dato que separa "la entrada es
buena pero el target es inalcanzable" de "la entrada está mal". Esas dos hipótesis
piden correcciones opuestas y hoy no hay forma de elegir entre ellas. Cuesta 30
segundos por operación y desbloquea todas las decisiones siguientes.

Con 30–40 operaciones registradas se responde:

- **MAE mediano de las ganadoras** → cuánto respiro necesitaba realmente el stop.
- **MFE mediano de las perdedoras** → si el target de 2R estaba al alcance.
- **% de perdedoras con MFE ≥ 1R** → si conviene parcializar o mover a BE.

---

## C2 · El stop se ancla al ATR, no a un número fijo de ticks

**Estado actual:** stop de 10 ticks fijos. Con ATR(14) M60 ≈ 0,32 (≈32 ticks), eso
es **0,31 × el rango medio de una hora**. El precio lo toca por ruido antes de que
la hipótesis se resuelva. 20 de 27 salidas reales fueron stop exacto.

**Corrección:**

```
stop (ticks) = máx( pivote a proteger , 0,5 × ATR(14) M60 en ticks )
target       = 2 × stop
riesgo $     = $100 fijo  (1 % de la cuenta de 10k)
tamaño       = $100 / (stop_ticks × valor_tick)
```

Se opera en **MCL** ($1/tick) para poder ajustar el tamaño con el stop ancho y
mantener el riesgo en dólares constante:

| ATR M60 | Stop mínimo | Target | Contratos MCL | Riesgo |
|---:|---:|---:|---:|---:|
| 0,30 | 15 tk | 30 tk | 6 | ~$100 |
| 0,40 | 20 tk | 40 tk | 5 | ~$100 |
| 0,50 | 25 tk | 50 tk | 4 | ~$100 |
| 0,60 | 30 tk | 60 tk | 3 | ~$100 |
| > 0,80 | — | — | **no se opera** | — |

**El coste honesto de este cambio:** la comisión de MCL es proporcionalmente más
cara ($1,84/contrato contra $5,32 por un CL que vale 10 veces más). Con 5 MCL la
comisión sube a $9,20 round-turn y el R neto baja de 1,85 a **1,75**, con lo que el
winrate de breakeven sube de 35,1 % a **36,4 %**. Se paga 1,3 puntos de winrate a
cambio de un stop entre 1,5 y 3 veces más ancho. Si el diagnóstico del ruido es
correcto, la compensación es muy favorable; el MFE/MAE de C1 lo confirmará o lo
desmentirá.

**Además:** la tabla de ATR del plan actual está escrita con los operadores
invertidos (`0<= ATR =>0.6`) y, con un ATR típico de 0,30–0,40, **siempre cae en el
primer tramo**. El segundo tramo (MCL, 20 ticks, 5 contratos) nunca se activó: todas
las operaciones registradas son CL 1 contrato con stop de 10. La regla de adaptación
a la volatilidad existía en el papel pero estaba muerta en la práctica. La tabla de
arriba la reemplaza.

---

## C3 · Fase de recalibración fuera de la cuenta de fondeo

**Estado actual:** el drawdown real acumulado fue de −$1.106 sobre los $2.000 que
permite la prueba. Con un winrate del 22 %, la probabilidad simulada de superarla es
**0,0 %**; incluso al 30 % es del 0,7 %.

**Corrección:** suspender la prueba de fondeo hasta cerrar la Fase 1. Operar en
**simulado o en cuenta propia con 1–2 MCL** (riesgo real $20–$40 por operación).

**Por qué:** validar una corrección exige entre 65 y 300 operaciones según de qué
tamaño sea la mejora. A $105 de riesgo por operación eso son entre $7.000 y $30.000
de exposición, imposible dentro de un drawdown de $2.000. La cuenta de fondeo no es
un lugar donde se investiga; es donde se cobra una ventaja ya demostrada. Pagar
suscripción mientras se investiga es pagar dos veces.

**Criterio de regreso al fondeo** (los tres a la vez):

1. ≥ 60 operaciones registradas con MFE/MAE completos bajo el plan corregido;
2. winrate ≥ 42 % (margen sobre el breakeven de 36,4 %, no empate);
3. profit factor ≥ 1,3 y drawdown máximo < 12R.

---

## C4 · Sólo ESTRUC+VC durante la Fase 1

**Estado actual:** ESTRUC+FV dio en vivo 12 operaciones, 16,7 % de winrate y −$664.
ESTRUC+VC dio 14 operaciones, 28,6 % y −$274. En backtest eran casi iguales
(52,9 % contra 59,0 %).

**Corrección:** operar únicamente **estructura + vela de confirmación**. La falta de
volumen queda suspendida y se sigue registrando en el diario como "señal observada
pero no operada", para poder evaluarla después sin arriesgar dinero.

**Por qué:** el disparador de falta de volumen es el más subjetivo de los dos —
cuál es "la vela de la corrección" es una decisión del operador—, y es justamente
el que más se degradó al pasar de backtest a vivo. Es el candidato natural a estar
inflado por el sesgo de hindsight.

---

## C5 · Ventana horaria

**Estado actual:** el plan fija dos horas desde la apertura cash. En vivo:

| Ventana | Real |
|---|---|
| 1.ª hora | n=7 · 42,9 % · **+$163** |
| 2.ª hora | n=17 · 17,6 % · **−$890** |
| pasadas las 2 h | n=3 · 0 % · −$216 |

**Corrección firme:** ninguna entrada pasados los 120 minutos desde la apertura
cash. Las 3 operaciones de mayo que rompieron esta regla perdieron las 3. Poner una
alarma al minuto 120 y cerrar plataforma.

**Corrección tentativa:** en la segunda hora, sólo setups ESTRUC+VC de calidad A.
Marcar la hora relativa a la apertura (no la hora de reloj) en cada registro y
revisar este corte a las 50 operaciones.

Advertencia deliberada: la primera hora tiene sólo 7 operaciones. **No es evidencia
suficiente para cerrar la segunda hora del todo**, y hacerlo cortaría a la mitad las
oportunidades justo cuando hacen falta operaciones para validar. Por eso el corte
firme es el de las 2 horas y el resto se mide.

Recordatorio operativo: la apertura cash se mueve con el horario de verano de EE.UU.
(10:00 BA en horario de verano, 11:00 BA fuera de él). Verificarlo cada marzo y cada
noviembre.

---

## C6 · Límite explícito de operaciones por sesión

**Estado actual:** el plan dice "Máximo de operaciones: sin límite" y a la vez fija
una pérdida máxima diaria de $200, que son exactamente 2 stops. La primera regla
contradice a la segunda.

**Corrección:**

- máximo **3 operaciones por sesión**;
- **2 stops completos cierran el día**, sin excepción;
- tras el segundo stop no se vuelve a mirar el gráfico hasta el día siguiente.

---

## C7 · No mover a break-even durante la Fase 1

**Estado actual:** el plan ya lo dice ("NO protegemos a BE en ningún momento"), y
en la Fase 1 hay que **mantenerlo**, aunque duela.

**Por qué:** mover a BE destruye el dato de MFE que hace falta para decidir. Si la
operación se cierra en BE nunca se sabe si habría llegado al target, y la corrección
C1 pierde todo su sentido. Primero se mide, después se optimiza la salida.

La decisión sobre parciales y BE se toma **al cerrar la Fase 1, con los datos de MFE
en la mano** — no antes. Si resulta que la mayoría de las perdedoras llegan a 1R
antes de girarse, el parcial se justifica solo; si no llegan, el parcial sólo
recortaría las ganadoras.

---

## Resumen de cambios

| # | Cambio | Impacto esperado | Confianza |
|---|---|---|---|
| C1 | Registrar MFE/MAE | Desbloquea el resto | **Alta** |
| C2 | Stop = 0,5 × ATR, tamaño en MCL | Ataca la causa principal | **Alta** |
| C3 | Salir del fondeo hasta validar | Evita la ruina | **Alta** |
| C4 | Sólo ESTRUC+VC | Quita el patrón más degradado | Media |
| C5 | Corte duro a los 120 min | Elimina 3 pérdidas evitables | Media |
| C6 | Máx. 3 ops / 2 stops por día | Resuelve una contradicción | Media |
| C7 | Sin BE durante la medición | Preserva la calidad del dato | **Alta** |

## Lo que hay que tener claro antes de empezar

Estas correcciones son razonables y salen de los datos, pero **ninguna está probada
todavía**. La corrección C2 es una hipótesis fuerte y bien fundada sobre la causa
—el stop está dentro del ruido—, no un hecho verificado. Puede pasar que con el stop
ancho el winrate suba y aun así no alcance el 36,4 % de breakeven, y en ese caso la
conclusión sería que el disparador no tiene ventaja predictiva y hay que rehacer la
entrada, no la gestión.

El objetivo de la Fase 1 no es ganar dinero: es **conseguir 60 operaciones con
MFE/MAE completos** para poder responder esa pregunta con datos en vez de con
intuición. Si al cabo de esas 60 operaciones el winrate sigue debajo de 36 %, la
respuesta honesta es que el sistema no es rentable tal como está y que el trabajo
siguiente está en la lógica de entrada.

Un último punto que conviene no perder de vista: 26 de las 27 operaciones reales
fueron ejecutadas según plan. La disciplina no es el problema acá.
