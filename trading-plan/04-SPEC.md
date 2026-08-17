# Especificación de la estrategia — para backtesting

Traducción del plan (`TPP-v2.md`) a **reglas de máquina**: cada decisión como algoritmo con
parámetros nombrados. Es la base para codificar en cualquier lenguaje (NinjaScript, Python).
No introduce reglas nuevas — sólo hace explícito y determinista lo que el plan describe.

> **Estado:** borrador v0. Los valores marcados `‹PARÁM›` son umbrales a congelar con
> Emiliano antes de correr (ver §9). Nada acá cambia el plan; si algo no coincide, manda el
> plan.

---

## 0 · Alcance: qué backtestea y qué no

| Parte | ¿En el backtest? |
|---|---|
| Tabla ATR → escenario, riesgo fijo, 2:1 | **Sí**, determinista |
| Ventana horaria, DST, topes día/semana | **Sí** |
| Set ups ESTRUC+VC, ESTRUC+FV, GIRO+VC | **Sí**, detector codificado (§5) |
| Gestión: bracket, stop/target, cierre bajo 1R, no-overnight | **Sí** |
| **Hipótesis A/B (contexto M60)** | **No automatizable** — es lectura discrecional. Se maneja como **filtro externo** (§8): v1 corre sin él y lo mide aparte. |

**Lo que Ankora aporta y lo que codificamos nosotros**

- Ankora (o su equivalente reproducido): niveles de sesión Europa, pivotes dinámicos,
  motor de gestión y stats. *No* detecta set ups.
- Nosotros: el **detector de set ups** (§5) y el arnés de backtest (topes, sizing, salidas).

---

## 1 · Datos de entrada

- **CL** (WTI). MCL = mismo subyacente; se backtestea sobre CL y se aplica valor de tick y
  comisión de MCL según el escenario (§4).
- Barras **M5** (detección y ejecución) y **M60** (ATR y contexto).
- **Volumen por barra** obligatorio (lo usa el disparador FV y el test de manipulación).
- Continuo por **rollover** en torno al día 18 (regla del plan). Guardar qué contrato es
  cada barra para no pegar saltos de precio.
- Marca de tiempo con **zona horaria del exchange** (para resolver sesiones y DST).

---

## 2 · Relojes y sesiones

```
apertura_cash(fecha)  = 09:00 ET  (hora del pit RTH de CL; verificar contra Ankora)
ventana_abre          = apertura_cash + 30 min      # §2.1 del plan
ventana_cierra        = apertura_cash + 150 min      # no se abren entradas después
cierre_sesion_cash    = ‹PARÁM: 14:30 ET / hora de aplanado no-overnight›   # §7.1
```

- Todo se convierte a la hora del exchange; el DST lo maneja la zona horaria, no un offset fijo.
- **Sesión Europa** (para el giro): `[europa_ini, europa_fin]` = `‹PARÁM›` (hora + zona,
  según config de Ankora del operador).

---

## 3 · Niveles

```
europa_high(d) = máx(High de barras M5 con time ∈ sesión Europa del día d)
europa_low(d)  = mín(Low  de barras M5 con time ∈ sesión Europa del día d)
```

**Pivote dinámico** (definición del TPP): máximo o mínimo de una sesión anterior **que aún
no fue roto**, más el máx/mín del **rango de apertura** de la sesión actual. Un pivote que
queda *dentro* de una sesión anterior a la actual no cuenta.

```
nivel_activo(nivel, hasta_t) = TRUE  si el precio no cerró del otro lado del nivel
                                      en la sesión en curso hasta t
```

Un nivel de Europa **roto durante la sesión** deja de contar como referencia/objetivo (§6.2.1, §1.4).

---

## 4 · Volatilidad y tamaño — la tabla (§1.3)

```
atr = ATR(14) sobre M60, leído en la preparación de sesión
escenario:
   atr <  500        → A: CL,  stop 15 tk, 1 contrato,  target 30 tk
   500 ≤ atr < 1000  → B: MCL, stop 30 tk, 5 contratos, target 60 tk
   1000 ≤ atr < 1250 → C: MCL, stop 50 tk, 3 contratos, target 100 tk
   1250 ≤ atr < 1500 → D: MCL, stop 75 tk, 2 contratos, target 150 tk
   atr ≥ 1500        → NO SE OPERA
```

(ATR en la escala de la plataforma: 500 = 0,500 $ = 50 ticks.) Riesgo ≈ $150 en los cuatro.
Comisión: CL $5,32 y MCL $1,84 por contrato (round turn). Valor de tick: CL $10, MCL $1.

---

## 5 · Detección de set ups (M5)

Todos comparten el **disparador** y la **entrada**; cambia la condición previa.

### 5.0 Disparador y entrada (común)

```
# caso ALCISTA (corto = espejo)
disparador_VC : vela verde cerrada (close > open)
disparador_FV : vela contraria al impulso cuyo volumen < volumen de las 2 velas previas
entrada       : orden LÍMITE; se dispara cuando una vela POSTERIOR supera el máximo de la
                vela disparador (rompe su high)
stop          : distancia fija del escenario (§4) desde la entrada
requisito     : el pivote a proteger (mín. del retroceso / mín. de la manipulación) debe
                quedar DENTRO del stop del escenario; si no, NO se opera (§1.3)
objetivo      : 2R del escenario; debe haber espacio hasta el próximo pivote dinámico
                Y hasta el nivel opuesto de Europa activo (§6.2.1)
```

### 5.1 ESTRUC+VC / ESTRUC+FV (estructura)

```
1. Hay un impulso en la dirección operada.
2. Retroceso: ≥1 vela contraria (roja en alcista) que confirma la corrección del impulso.
   NO se exige que el retroceso llegue a un nivel de relevancia.
3. Disparador: VC (ESTRUC+VC) o FV (ESTRUC+FV) según §5.0.
4. Entrada por §5.0.
```
*(ESTRUC+FV: activo pero de baja frecuencia; ESTRUC+VC es el principal.)*

### 5.2 GIRO+VC (§6.2.1 — los 5 pasos)

```
# alcista, sobre europa_low(d):
1. MANIPULACIÓN: una vela PERFORA europa_low (low < europa_low − ‹PARÁM: 1 tick›)   # toque no vale
   y muestra rechazo:  mecha_inferior ≥ ‹PARÁM: 60%› del rango de la vela
                       OR volumen ≥ ‹PARÁM: 1,5×› la mediana de las últimas ‹N=20› velas
2. REINGRESO: una vela posterior cierra de nuevo por encima de europa_low.
   INVALIDA si antes se forma una base por debajo durante > ‹PARÁM: K=6› velas M5.
3. RETROCESO: ≥1 vela roja; válido mientras ninguna vela CIERRE por debajo del mínimo de
   la manipulación. Si una cierra por debajo → giro cancelado.
4. CONFIRMACIÓN: primera vela verde cerrada.
5. ENTRADA: por §5.0 (rompe el máximo de la verde), con stop del escenario debajo del
   pivote (mín. de la manipulación).
# GIRO+FV: ELIMINADO del plan — no se detecta.
```

---

## 6 · Gestión de la operación

```
al entrar: bracket OCO {entrada, stop escenario, target 2R}
mientras abierta: no se toca (el bracket decide)
en ventana_cierra (+150): no se abren nuevas; las abiertas siguen con su bracket
en cierre_sesion_cash: si sigue abierta → aplanar a mercado (no-overnight)   # §7.1
```

Registro por operación (para stats): entrada, salida, dirección, escenario, set up, ticks,
$, R, **MFE, MAE**, duración, si cerró por stop/target/aplanado.

---

## 7 · Topes y estado (§1.5)

```
por día:    máx 2 operaciones; 2 stops (−2R) cierran el día
por semana: neto acumulado en R; si toca −3R → semana cerrada
por mes:    lo gobierna el drawdown de la cuenta (no hay tope propio)
```

Máquina de estados que arrastra R diario y semanal y bloquea nuevas entradas al tocar el tope.

---

## 8 · Filtro de hipótesis A/B

No se automatiza en v1. Tres formas de tratarlo, en orden de preferencia:

1. **Correr sin el filtro** y medir la ventaja cruda de cada set up. Si ya es positiva, el
   filtro sólo puede mejorarla.
2. **Proxy de contexto** (opcional): tendencia/estructura simple en M60 (p.ej. posición
   respecto de EMA o de los extremos de la semana) como aproximación de A/B — se mide su
   aporte por separado, sabiendo que no replica tu lectura.
3. **Semi-automático:** el código marca los candidatos y un humano etiqueta la hipótesis.

---

## 9 · Parámetros a congelar (con Emiliano)

| Parámetro | Dónde | Valor propuesto |
|---|---|---|
| Horario sesión Europa (ini/fin + zona) | §2, §3 | ‹de la config de Ankora› |
| Hora de aplanado no-overnight | §2 | ‹regla de la cuenta de fondeo› |
| Perforación mínima de la manipulación | §5.2 | 1 tick |
| Mecha de rechazo | §5.2 | ≥ 60 % del rango de la vela |
| Volumen de manipulación | §5.2 | ≥ 1,5× mediana de 20 velas |
| "Base considerable" que invalida el reingreso | §5.2 | > 6 velas M5 |
| Volumen FV | §5.0 | menor que las 2 velas previas (regla del plan) |
| Umbrales de ATR | §4 | 500 / 1000 / 1250 / 1500 (ya fijados) |

---

## 10 · Validación obligatoria antes de confiar en el backtest largo

Correr el detector sobre el **período de las 97 operaciones reales** (22/10/2025 →
26/06/2026) y comparar contra el registro B20x50:

- ¿El código encuentra las mismas entradas (fecha/hora/dirección/set up)?
- ¿El resultado por operación coincide?

Si coincide razonablemente, el backtest largo es creíble. Si no, se ajustan las reglas de
§5 hasta que reproduzca lo conocido. Recién ahí se corre sobre años.

---

## 11 · Salidas del backtest

- **Trade log** completo con MFE/MAE por operación (responde 2:1 vs 2,5:1 y parciales a
  escala).
- Stats por set up / escenario / hora / día: winrate, R, profit factor, drawdown, rachas.
- Curva de equity y, sobre muestras grandes, potencia estadística real (lo que con 97
  operaciones no alcanzaba).

---

## Ruta de implementación sugerida

1. **Este spec** (v0) → congelar §9 con Emiliano.
2. Export de datos CL (M5+M60+volumen, años) desde NinjaTrader.
3. Detector + arnés en **Python** (mejor para stats) sobre el CSV; niveles de Europa y
   pivotes reproducidos con las definiciones de §3.
4. **Validación §10** contra las 97.
5. Backtest largo + análisis.
6. *(Opcional)* portar el detector validado a NinjaScript para operarlo/automatizarlo en NT.
