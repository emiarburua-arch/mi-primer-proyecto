# Corrección importante — el edge del giro era un artefacto

## Qué pasó

Al llevar el giro a NinjaTrader (bot real), **dos implementaciones independientes** (entrada a
mercado y entrada con orden stop) dieron **~30-35 % de aciertos y resultado breakeven/negativo**.
Mi backtest de Python daba **56 % y +0,63 R/trade**. Cuando la ejecución real contradice al
backtest de forma consistente, el error está en el backtest.

Reimplementé el giro en Python **fiel a una orden real** (se arma una orden que descansa en el
nivel y se llena cuando el precio lo cruza, sin re-elegir el disparador cada vela). Resultado:

| Modelo | n | WR | R/trade | PF |
|---|---|---|---|---|
| Backtest original (optimista) | 651 | 56 % | +0,68 | 2,54 |
| **Fiel a orden real (correcto)** | 488 | 34 % | **+0,02** | 1,03 |
| NinjaTrader (v1 y v2) | ~130 | 30-35 % | negativo | 0,86-1,15 |

Por fuente (fiel, 2R): Asia +0,03 · Europa −0,07 · NY −0,05. A objetivo 1R/1,5R/2R: todo
breakeven o negativo. **El giro mecánico no tiene edge.**

## El artefacto

El simulador original, en cada vela, **volvía a elegir el disparador** (la vela de confirmación)
y entraba en la vela donde el patrón "se completaba", al precio justo del nivel. Eso equivale a
elegir la entrada con el diario del lunes — un beneficio que **una orden real no puede tener**:
la orden se compromete a UN nivel por adelantado y se llena donde el mercado la lleva, muchas
veces justo antes de que revierta. Al comprometerse (como el bot), el edge desaparece.

## Qué implica

- **Un bot 100 % mecánico sobre estas reglas no es rentable.** El giro y el ESTRUC mecánicos son
  breakeven (con comisión, ligeramente negativos).
- El edge —si existe— está en la **parte discrecional** (qué giros tomar, estructura, hipótesis)
  que no logramos mecanizar. Los números discrecionales reales del operador también fueron
  negativos, pero eso estaba mezclado con el problema de sizing.
- **Se descubrió en validación, no con plata real.** Para eso sirve validar.

## Estado de los documentos previos

Los resultados de `08-BACKTEST-extendido.md`, `10-AUTO-GIRO.md` y `11-SISTEMA-completo.md` están
**sobreestimados** (usan el modelo optimista). Hay que recalcularlos con el modelo fiel antes de
confiar en cualquier número. La gestión (sizing, topes, aplanado) sigue siendo válida; lo que se
cae es el *edge de la señal*.
