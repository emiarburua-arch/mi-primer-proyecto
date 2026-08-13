# Trading Plan Personal — v2

**Emiliano Arburua** · CL / MCL · Metodología Ankora
Basado en el TPP vigente y en el análisis de 97 operaciones reales (22/10/2025 → 26/06/2026).

> Estado: **en construcción**. Los bloques marcados `[PENDIENTE]` esperan definición.

---

## 0 · Objetivo y horizonte

**Objetivo de esta etapa: validar las correcciones en 40–60 operaciones.**

El éxito de esta fase no se mide en dinero sino en dos números:

| Métrica | Hoy | Objetivo |
|---|---:|---:|
| R realizado | 1,53 | **≥ 1,85** |
| Winrate | 35,4 % | **≥ 35 %** (que no baje) |

Si el R sube a 1,85 y el winrate aguanta, el sistema es rentable y recién ahí tiene
sentido hablar de objetivos de dinero. Si el R sube pero el winrate cae por debajo del
33 %, la hipótesis está mal y hay que volver sobre la entrada.

**Vehículo: prueba de fondeo.** A ~1,2 operaciones por día, 50 operaciones son unos dos
meses de operativa.

---

## 1 · Gestión del riesgo

### 1.1 Instrumentos

CL y MCL. La elección no es por preferencia sino por volatilidad: define el escenario
(§1.3), y el escenario define el instrumento.

### 1.2 Riesgo por operación

**$150 fijos por operación.** El importe no se mueve dentro del mes; se recalcula el 1º de
cada mes según el capital de la cuenta.

Que sea fijo es justamente el punto: es lo que hace que los cuatro escenarios de §1.3
arriesguen exactamente lo mismo. **Este es el principio que no se negocia.**

### 1.3 Escenarios de volatilidad — **la tabla**

Se lee el **ATR(14) en M60** antes de la sesión. Ese número decide todo lo demás: no hay
nada que improvisar durante la operativa.

| ATR M60 | Escenario | Stop | Instrumento | Contratos | **Target** | Riesgo | Gana | Pierde |
|---|:-:|---:|:-:|---:|---:|---:|---:|---:|
| **< 500** | **A** | **15 tk** | CL | **1** | **30 tk** | $150 | +$294,68 | −$155,32 |
| **500 – 1000** | **B** | **30 tk** | MCL | **5** | **60 tk** | $150 | +$290,80 | −$159,20 |
| **1000 – 1250** | **C** | **50 tk** | MCL | **3** | **100 tk** | $150 | +$294,48 | −$155,52 |
| **1250 – 1500** | **D** | **75 tk** | MCL | **2** | **150 tk** | $150 | +$296,32 | −$153,68 |
| **> 1500** | — | **no se opera** | | | | | | |

El ATR se lee en la escala de la plataforma (milésimas de dólar): **500 = 0,500 = 50
ticks** de rango medio por hora.

El riesgo da **$150 exactos en los cuatro casos**: 15 × $10 = 30 × $5 = 50 × $3 = 75 × $2.
Esa igualdad es toda la corrección — el año pasado el riesgo real fue de $121,63 cuando la
operación ganaba y $155,79 cuando perdía, y esos 28 puntos de diferencia se llevaron el R
de 2,00 a 1,53.

**El stop es el del escenario, no el que pida el gráfico.** Si el pivote a proteger queda
más lejos que el stop de la tabla, la operación **no se toma**. Esta es la regla que más
operaciones va a descartar: sobre el histórico habrías tomado 68 de 96. Las 28 que quedan
fuera dieron 3 ganadoras y 9 perdedoras entre las de stop ancho, con −$518 de resultado,
así que el filtro no está dejando fuera nada bueno.

| | R neto | Winrate de equilibrio |
|:-:|---:|---:|
| A | 1,90 | 34,5 % |
| B | 1,83 | 35,4 % |
| C | 1,89 | 34,6 % |
| D | 1,93 | 34,2 % |

El escenario B es el menos eficiente: cinco micros pagan $9,20 de comisión contra los
$3,68 de dos. No hay nada que hacer al respecto —es el precio de operar con ATR medio—
pero conviene saber que ahí el margen es más fino.

### 1.4 Ratio

**2:1 siempre.** Comprobado sobre las capturas: las ganadoras alcanzaron entre 2,11R y
3,05R, con lo que el objetivo a 2R captura casi todo el movimiento disponible. Estirarlo a
2,5R habría convertido tres de cada cuatro ganadoras en pérdidas completas.

Si el pivote objetivo no permite 2:1 desde el stop del escenario, **no hay operación**.

### 1.5 Topes

| | |
|---|---|
| Operaciones por día | **máximo 2** |
| Pérdida diaria | **2 stops ($300) cierran el día** |
| Pérdida semanal | `[PENDIENTE — bloque 2]` |
| Pérdida mensual | `[PENDIENTE — bloque 2]` |

Después del segundo stop no se vuelve a mirar el gráfico hasta el día siguiente.

---

## 2 · Mercado, días y horarios

### 2.1 Ventana operativa

`[PENDIENTE — bloque 2]`

**Regla firme del análisis:** la ventana **abre a los 30 minutos** de la apertura cash.
Trece operaciones en la primera media hora, una sola ganadora, −$1.448 (Fisher p = 0,029).
Esa media hora es de observación.

Recordatorio: la apertura cash se mueve entre las 10:00 y las 11:00 de Buenos Aires con el
horario de verano de EE.UU. Recalcular en **noviembre** y en **marzo**.

### 2.2 Días que no se opera

`[PENDIENTE — bloque 2]`

---

## 3 · Contexto — trazado de niveles M60

*(Del plan vigente, sin cambios: el winrate se mantuvo estable en 35–36 % durante ocho
meses, así que la lectura funciona.)*

- Máximo y mínimo del mes anterior
- Cierre del mes anterior
- Máximo y mínimo de la semana anterior
- Zona de inflexión
- Máximo y mínimo del lunes de la semana en curso
- Apertura semanal
- Apertura diaria
- Soporte relevante para el contexto

### 3.1 Lectura mensual

Dónde está el precio respecto de los máximos y mínimos del mes anterior. Si hubo
manipulaciones o acumulación en alguno de los niveles. Por encima o por debajo del cierre
del mes anterior. ¿Estamos por encima del máximo, dentro del rango, por debajo del mínimo?
¿En qué semana del mes estamos?

### 3.2 Lectura semanal

Con los máximos y mínimos de las semanas anteriores, en qué día de la semana estamos.
¿Por encima del máximo de la semana anterior, dentro del rango, por debajo del mínimo?
¿Hay manipulaciones de máximos o mínimos? ¿Por encima o debajo de la apertura semanal y de
la apertura del día? ¿Hay dirección clara hacia alguno de los extremos de la semana
anterior?

### 3.3 Zona de inflexión

Zona que, de ser superada o perforada, invalida la dirección que traía el mercado.

### 3.4 Hipótesis

- **Hipótesis A** — hacia dónde será dirigido el precio y desde dónde puedo operar en esa dirección.
- **Hipótesis B** — desde qué nivel estoy habilitado a operar en dirección contraria, y por qué.

---

## 4 · Trazado de niveles M5

- Máximos y mínimos de sesión asiática, europea y americana
- Pivotes dinámicos
- Apertura cash

---

## 5 · Toma de operación

### 5.1 Requisitos previos

Antes de mandar la orden:

- [ ] Ventana de oportunidad revisada
- [ ] Escenario del día definido (§1.3) → stop, instrumento y contratos ya fijados
- [ ] Objetivo identificado y **verificado que permite 2:1 desde el stop**
- [ ] Han pasado 30 minutos desde la apertura cash

### 5.2 Set ups

| Set up | Estado | Motivo |
|---|---|---|
| Estructura + Vela de confirmación | **Activo** | 52 ops, 36,5 % |
| Estructura + Falta de volumen | **Activo** | 8 ops, 50,0 % |
| Giro + Vela de confirmación | **Activo** | 30 ops, 36,7 % — mismo acierto que ESTRUC+VC |
| Giro + Falta de volumen | `[PENDIENTE — bloque 3]` | 6 ops, 0 ganadoras, −$946 |

Para Giro se usa manipulación (UT o SP) en un nivel relevante, en general máximo o mínimo
de sesión anterior.

Los pivotes dinámicos se usan como objetivos: para tomar una operación, el pivote tiene que
permitir el recorrido hasta el target.

### 5.3 Ejecución

Orden limitada.

---

## 6 · Gestión de la posición

Una vez dentro, **no se toca la operación hasta que cierre**.

### 6.1 La excepción, ahora con límite

`[PENDIENTE — bloque 3]`

El plan vigente permite cerrar «si la operación se demora, no cierra por sí sola y debemos
dejar la sesión». Sin límite, esa excepción costó cuatro ganadoras que cobraron entre
0,03R y 0,21R: el 12 % de las ganadoras del año aportando $69 donde correspondían ~$1.200.

---

## 7 · Registro

`[PENDIENTE — bloque 4]`

**Obligatorio y hoy ausente:** MFE y MAE en cada operación. Están vacíos en 96 de 97.

---

## 8 · Cierre de sesión

- Verificar que esté todo documentado
- Captura de pantalla de la sesión, guardada
- `[PENDIENTE — bloque 4]`

---

## 9 · Revisión y criterios de parada

`[PENDIENTE — bloque 4]`

---

## 10 · Plan de contingencia

`[PENDIENTE — bloque 4]`
