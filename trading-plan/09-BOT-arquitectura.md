# Del backtest al bot operativo (NinjaTrader)

Cómo llevar **el sistema completo** (no el setup aislado) a un bot en NinjaTrader, que sirva
tanto para **backtest en el Strategy Analyzer** como para **operar en vivo/sim**.

## La buena noticia: una sola estrategia sirve para las dos cosas

En NinjaTrader, una clase `Strategy` de **NinjaScript (C#)** corre:

- en el **Strategy Analyzer** → backtest sobre histórico,
- en un **chart con cuenta** → en vivo o en **Sim101** (paper trading).

**Es el mismo código.** No se programa dos veces. Lo que validás en backtest es exactamente lo
que después opera.

## El sistema completo — lo que el bot debe implementar como un todo

No es "detectar el giro". Es toda la cadena del plan (`TPP-v2.md`):

| Módulo | Qué hace | Estado |
|---|---|---|
| **Volatilidad / sizing** | ATR(14) M60 → escenario → instrumento, stop, contratos, target. Riesgo $150 fijo | ✅ definido y backtesteado |
| **Relojes** | Ventana operativa (apertura NY +30…+150), sesión Europa (niveles), aplanado 18:00 BA | ✅ congelado |
| **Setups** | GIRO+VC (principal), ESTRUC+VC (secundario). FV afuera | ✅ backtesteado |
| **Ejecución** | Orden límite al romper el disparador + bracket OCO (stop + 2R). No se toca | ✅ definido |
| **Estado / topes** | Máx 2 trades/día, −2R día, −3R semana, no-overnight | ✅ definido |
| **Contexto** | Estructura HH+HL, hipótesis A/B (M60) | ⚠️ **discrecional** |

La gestión (sizing constante, bracket, topes, aplanado) es la parte que **el bot hace perfecto**
— y es exactamente donde tus números reales se rompían (riesgo inconsistente, cerrar por horario).

## El fork que define todo: ¿mecánico total o semi-automático?

El sistema tiene partes **discrecionales que medimos y NO se automatizan bien**: la lectura de
estructura (proxy mecánico ~50-60 %) y la hipótesis A/B (el filtro M60 no aportó). Entonces:

### Opción A — Bot 100 % mecánico
Implementa las reglas mecánicas exactas que backtesteamos. **Es operable** (el giro mecánico
tiene edge real, +0,39 R, positivo todos los años). Pero:
- toma **muchos más trades** que vos (el detector de giro dispara 392 vs tus ~30 selectivos),
- opera **sin** tu filtro de estructura/hipótesis.

### Opción B — Asistente semi-automático
El bot hace **toda la gestión** (detecta candidatos, calcula sizing por ATR, arma el bracket,
lleva los topes, aplana) y **vos confirmás la entrada** con tu lectura discrecional.
- respeta cómo operás de verdad,
- elimina los errores de sizing/gestión que te costaron plata,
- es el puente natural entre tu operativa manual y la automatización.

### Recomendación
- **Vivo/Sim → empezar por B.** Automatiza lo que fallaba (gestión) y mantiene tu criterio.
- **Backtest en NT → A.** Versión mecánica pura, para validar contra el backtest de Python.

## Riesgo de fidelidad: Python ↔ NinjaScript

Nuestro backtest está en Python con definiciones propias (resampling M5, niveles de Europa, ATR,
sesiones en UTC/ET). NinjaScript calcula todo eso nativo, pero **hay que validar que la estrategia
NinjaScript reproduce los mismos resultados** antes de confiar (mismas entradas, mismos R).
Diferencias posibles: resampleo de barras, zona horaria, modelo de fill intrabar. Es la §10 del
spec, ahora entre lenguajes.

## Un detalle técnico: CL vs MCL en una sola estrategia

La tabla ATR usa **CL** en el escenario A y **MCL** en B/C/D. Pero una `Strategy` de NinjaScript
va atada a **un** instrumento. Cambiar de símbolo por escenario es engorroso. Solución limpia:
**operar siempre MCL (micros)** y escalar contratos — el escenario A sería ~10 MCL en vez de 1 CL
(misma exposición, un poco más de comisión). Así el bot vive en un solo instrumento y la tabla se
vuelve "todo en MCL". A confirmar con vos.

## Roadmap por etapas

1. **Esqueleto del sistema** en NinjaScript: sizing por ATR + ventanas + topes + bracket +
   aplanado, con entrada **manual** (un botón / una tecla). Esto ya te automatiza la **gestión**
   —lo más valioso— sin depender de la detección.
2. **Detección mecánica** de GIRO+VC y ESTRUC+VC integrada.
3. **Validación** en Strategy Analyzer contra el backtest de Python.
4. **Sim101 (paper)** en modo B (semi-auto) o A (full-auto).
5. **Métricas en vivo** y ajuste.

## Qué necesito de vos para arrancar

1. **La decisión A vs B** (mecánico total vs semi-automático) para el modo en vivo.
2. **Instrumento/cuenta:** ¿operamos todo en MCL? ¿cuál es tu cuenta de fondeo y sus reglas
   (horario de aplanado, límites)? ¿Sim101 para las pruebas?
3. **Los giros sobre pivotes** (el ⅓ fuera de Europa): ¿los sumamos al detector o el bot opera
   solo los de Europa?
