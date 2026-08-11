# Fase 1 — checklist operativo

Objetivo de la fase: **60 operaciones con MFE y MAE completos**, en simulado o con
1–2 MCL. No es una fase de ganar dinero, es una fase de medir.

---

## Antes de la sesión

- [ ] ATR(14) en M60 leído y anotado (en ticks, no en la escala del indicador).
- [ ] Stop de hoy calculado: `máx(pivote, 0,5 × ATR)`. Target = 2 × stop.
- [ ] Contratos MCL calculados para que el riesgo quede en el importe fijo de la fase.
- [ ] Si ATR > 0,80 → **no se opera**. Anotarlo igual en el registro.
- [ ] Hora de apertura cash verificada (10:00 BA en horario de verano de EE.UU., 11:00 fuera).
- [ ] Alarma puesta al **minuto 120** desde la apertura.
- [ ] Calendario de noticias revisado (inventarios de crudo → no se opera).
- [ ] Meditación y diario emocional, como en el plan original.

## Durante

- [ ] Sólo **ESTRUC+VC**. La falta de volumen se anota como señal observada, no se opera.
- [ ] Máximo **3 operaciones**; **2 stops cierran el día**.
- [ ] **No mover a break-even.** Aunque duela. Es lo que preserva el dato de MFE.
- [ ] Nada de entradas pasado el minuto 120.

## Al cerrar cada operación — obligatorio

Sin estos dos campos la operación no cuenta para la muestra de 60:

- [ ] **MFE** — máximo recorrido a favor, en ticks, desde el precio de entrada.
- [ ] **MAE** — máximo recorrido en contra, en ticks, desde el precio de entrada.
- [ ] ATR de la sesión, stop en ticks y contratos usados.
- [ ] **Minutos desde la apertura cash** (no la hora de reloj — el horario se mueve dos veces al año).
- [ ] Patrón, dirección, resultado en ticks.

## Revisión a las 30 operaciones

Primer corte de diagnóstico. Calcular:

| Métrica | Qué decide |
|---|---|
| MAE mediano de las **ganadoras** | cuánto respiro necesitaba el stop de verdad |
| MFE mediano de las **perdedoras** | si el target de 2R estaba al alcance |
| % de perdedoras con MFE ≥ 1R | si conviene parcializar o mover a BE |
| Winrate por hora relativa | si la segunda hora se cierra o se mantiene |

Con esto se ajusta el target y se decide sobre parciales. **Recién acá**, no antes.

## Revisión a las 60 operaciones — criterio de salida

Se vuelve a la cuenta de fondeo sólo si se cumplen las tres a la vez:

- [ ] 60 operaciones con MFE/MAE completos bajo el plan corregido
- [ ] Winrate ≥ **42 %** (margen sobre el equilibrio de 36,4 %, no empate)
- [ ] Profit factor ≥ **1,3** y drawdown máximo < 12R

Si el winrate sigue por debajo del 36 % con el stop ancho, la respuesta honesta es que
el problema está en la lógica de entrada y no en la gestión. Eso no es un fracaso de la
fase: es exactamente lo que la fase servía para averiguar, y averiguarlo con 2 micros
cuesta unos cientos de dólares en vez de varias suscripciones de fondeo.
